import webauthn

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..forms import RegisterKeyForm
from .. import util


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def webauthn_begin_activate(request):
    if 'register_ukey' in request.session:
        del request.session['register_ukey']
    if 'challenge' in request.session:
        del request.session['challenge']

    form = RegisterKeyForm(request.POST)

    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)

    username = request.user.get_username()
    display_name = request.user.get_full_name()

    challenge = util.generate_challenge(32)
    ukey = util.generate_ukey()

    request.session['key_name'] = form.cleaned_data["key_name"]
    request.session['challenge'] = challenge
    request.session['register_ukey'] = ukey

    make_credential_options = webauthn.WebAuthnMakeCredentialOptions(
        challenge, settings.RELYING_PARTY_NAME, settings.RELYING_PARTY_ID,
        ukey, username, display_name, settings.WEBAUTHN_ICON_URL,
    )

    return JsonResponse(make_credential_options.registration_dict)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def webauthn_verify_credential_info(request):
    print(request.POST)
    return JsonResponse(request.POST)
