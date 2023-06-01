from django.conf import settings as django_settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

from .. import settings, utils
from ..forms import KeyRegistrationForm
from ..models import WebAuthnKey
from ..utils import webauthn

# Registration


@login_required
@require_http_methods(["GET"])
def webauthn_begin_activate(request):
    challenge = webauthn.generate_webauthn_challenge()

    request.session["challenge"] = bytes_to_base64url(challenge)

    credential_options = webauthn.get_credential_options(
        request.user,
        challenge=challenge,
        rp_name=settings.RELYING_PARTY_NAME,
        rp_id=settings.RELYING_PARTY_ID,
    )

    return JsonResponse(credential_options)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def webauthn_verify_credential_info(request):
    challenge = base64url_to_bytes(request.session["challenge"])
    credentials = request.POST["credentials"]

    form = KeyRegistrationForm(request.POST)

    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    try:
        webauthn_registration_response = webauthn.verify_registration_response(
            credentials,
            rp_id=settings.RELYING_PARTY_ID,
            origin=utils.get_origin(request),
            challenge=challenge,
        )
    except webauthn.RegistrationRejectedError as e:
        return JsonResponse({"fail": f"Registration failed. Error: {e}"}, status=400)

    # W3C spec. Step 17.
    #
    # Check that the credentialId is not yet registered to any other user.
    # If registration is requested for a credential that is already registered
    # to a different user, the Relying Party SHOULD fail this registration
    # ceremony, or it MAY decide to accept the registration, e.g. while deleting
    # the older registration.
    credential_id_exists = WebAuthnKey.objects.filter(
        credential_id=bytes_to_base64url(webauthn_registration_response.credential_id)
    ).first()
    if credential_id_exists:
        return JsonResponse({"fail": "Credential ID already exists."}, status=400)

    WebAuthnKey.objects.create(
        user=request.user,
        key_name=form.cleaned_data["key_name"],
        public_key=bytes_to_base64url(
            webauthn_registration_response.credential_public_key
        ),
        credential_id=bytes_to_base64url(webauthn_registration_response.credential_id),
        sign_count=webauthn_registration_response.sign_count,
    )

    try:
        del request.session["challenge"]
        del request.session["key_name"]
    except KeyError:  # pragma: no cover
        pass

    return JsonResponse({"success": "User successfully registered."})


# Login
@require_http_methods(["GET"])
def webauthn_begin_assertion(request):
    challenge = webauthn.generate_webauthn_challenge()
    request.session["challenge"] = bytes_to_base64url(challenge)

    user = utils.get_user(request)

    webauthn_assertion_options = webauthn.get_assertion_options(
        user, challenge=challenge, rp_id=settings.RELYING_PARTY_ID
    )

    return JsonResponse(webauthn_assertion_options)


@csrf_exempt
@require_http_methods(["POST"])
def webauthn_verify_assertion(request):
    challenge = base64url_to_bytes(request.session.get("challenge"))

    user = utils.get_user(request)

    try:
        webauthn_assertion_response = webauthn.verify_assertion_response(
            request.POST["credentials"],
            challenge=challenge,
            user=user,
            origin=utils.get_origin(request),
            rp_id=settings.RELYING_PARTY_ID,
        )
    except webauthn.AuthenticationRejectedError as e:
        return JsonResponse({"fail": f"Assertion failed. Error: {e}"}, status=400)

    # Update counter.
    key = user.webauthn_keys.get(
        credential_id=bytes_to_base64url(webauthn_assertion_response.credential_id)
    )
    key.sign_count = webauthn_assertion_response.new_sign_count
    key.last_used = now()
    key.save()

    try:
        del request.session["kagi_pre_verify_user_pk"]
        del request.session["kagi_pre_verify_user_backend"]
        del request.session["challenge"]
    except KeyError:  # pragma: no cover
        pass

    auth.login(request, user)

    redirect_to = request.POST.get(
        auth.REDIRECT_FIELD_NAME, request.GET.get(auth.REDIRECT_FIELD_NAME, "")
    )
    if not url_has_allowed_host_and_scheme(
        url=redirect_to, allowed_hosts=[request.get_host()]
    ):
        redirect_to = resolve_url(django_settings.LOGIN_REDIRECT_URL)

    return JsonResponse(
        {
            "success": f"Successfully authenticated as {user.get_username()}",
            "redirect_to": redirect_to,
        }
    )
