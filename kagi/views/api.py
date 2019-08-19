from django.conf import settings as django_settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import resolve_url
from django.utils.http import is_safe_url
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

import webauthn

from .. import settings, util
from ..forms import KeyRegistrationForm
from ..models import WebAuthnKey

# Registration


@login_required
@require_http_methods(["POST"])
def webauthn_begin_activate(request):
    form = KeyRegistrationForm(request.POST)

    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    username = request.user.get_username()
    display_name = request.user.get_full_name()

    challenge = util.generate_challenge(32)
    ukey = util.generate_ukey()

    request.session["key_name"] = form.cleaned_data["key_name"]
    request.session["challenge"] = challenge
    request.session["register_ukey"] = ukey

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge,
        settings.RELYING_PARTY_NAME,
        settings.RELYING_PARTY_ID,
        ukey,
        username,
        display_name,
        settings.WEBAUTHN_ICON_URL,
    )

    return JsonResponse(make_credential_options.registration_dict)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def webauthn_verify_credential_info(request):
    challenge = request.session["challenge"]
    ukey = request.session["register_ukey"]

    registration_response = request.POST
    trust_anchor_dir = settings.WEBAUTHN_TRUSTED_CERTIFICATES
    trusted_attestation_cert_required = (
        settings.WEBAUTHN_TRUSTED_ATTESTATION_CERT_REQUIRED
    )
    self_attestation_permitted = settings.WEBAUTHN_SELF_ATTESTATION_PERMITTED
    none_attestation_permitted = settings.WEBAUTHN_NONE_ATTESTATION_PERMITTED

    webauthn_registration_response = webauthn.WebAuthnRegistrationResponse(
        settings.RELYING_PARTY_ID,
        util.get_origin(request),
        registration_response,
        challenge,
        trust_anchor_dir,
        trusted_attestation_cert_required,
        self_attestation_permitted,
        none_attestation_permitted,
        uv_required=False,  # User validation
    )

    try:
        webauthn_credential = webauthn_registration_response.verify()
    except Exception as e:
        return JsonResponse(
            {"fail": "Registration failed. Error: {}".format(e)}, status=400
        )

    # W3C spec. Step 17.
    #
    # Check that the credentialId is not yet registered to any other user.
    # If registration is requested for a credential that is already registered
    # to a different user, the Relying Party SHOULD fail this registration
    # ceremony, or it MAY decide to accept the registration, e.g. while deleting
    # the older registration.
    credential_id_exists = WebAuthnKey.objects.filter(
        credential_id=webauthn_credential.credential_id.decode("utf-8")
    ).first()
    if credential_id_exists:
        return JsonResponse({"fail": "Credential ID already exists."}, status=400)

    WebAuthnKey.objects.create(
        user=request.user,
        key_name=request.session.get("key_name", ""),
        ukey=ukey,
        public_key=webauthn_credential.public_key.decode("utf-8"),
        credential_id=webauthn_credential.credential_id.decode("utf-8"),
        sign_count=webauthn_credential.sign_count,
    )

    try:
        del request.session["challenge"]
        del request.session["register_ukey"]
        del request.session["key_name"]
    except KeyError:  # pragma: no cover
        pass

    return JsonResponse({"success": "User successfully registered."})


# Login
@require_http_methods(["POST"])
def webauthn_begin_assertion(request):
    # TODO: The challenge could be different for each key
    challenge = util.generate_challenge(32)
    request.session["challenge"] = challenge

    user = util.get_user(request)

    username = user.get_username()
    display_name = user.get_full_name()

    keys = WebAuthnKey.objects.filter(user=user)

    assertions = []
    for key in keys:
        webauthn_user = webauthn.WebAuthnUser(
            key.ukey,
            username,
            display_name,
            settings.WEBAUTHN_ICON_URL,
            key.credential_id,
            key.public_key,
            key.sign_count,
            settings.RELYING_PARTY_ID,
        )
        webauthn_assertion_options = webauthn.WebAuthnAssertionOptions(
            webauthn_user, challenge
        )
        assertions.append(webauthn_assertion_options.assertion_dict)

    return JsonResponse({"assertion_candidates": assertions})


@csrf_exempt
@require_http_methods(["POST"])
def webauthn_verify_assertion(request):
    challenge = request.session.get("challenge")
    assertion_response = request.POST
    credential_id = assertion_response.get("id")

    user = util.get_user(request)

    username = user.get_username()
    display_name = user.get_full_name()

    key = WebAuthnKey.objects.filter(credential_id=credential_id, user=user).first()
    if not key:
        return JsonResponse({"fail": "Key does not exist."}, status=400)

    webauthn_user = webauthn.WebAuthnUser(
        key.ukey,
        username,
        display_name,
        settings.WEBAUTHN_ICON_URL,
        key.credential_id,
        key.public_key,
        key.sign_count,
        settings.RELYING_PARTY_ID,
    )

    webauthn_assertion_response = webauthn.WebAuthnAssertionResponse(
        webauthn_user,
        assertion_response,
        challenge,
        util.get_origin(request),
        uv_required=False,  # User Verification
    )

    try:
        sign_count = webauthn_assertion_response.verify()
    except Exception as e:
        return JsonResponse(
            {"fail": "Assertion failed. Error: {}".format(e)}, status=400
        )

    # Update counter.
    key.sign_count = sign_count
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
    if not is_safe_url(url=redirect_to, allowed_hosts=[request.get_host()]):
        redirect_to = resolve_url(django_settings.LOGIN_REDIRECT_URL)

    return JsonResponse(
        {
            "success": "Successfully authenticated as {}".format(user.username),
            "redirect_to": redirect_to,
        }
    )
