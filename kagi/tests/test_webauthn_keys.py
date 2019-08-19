from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse

import pytest

from .. import settings
from ..forms import KeyRegistrationForm
from ..models import WebAuthnKey


def test_list_webauthn_keys(admin_client):
    response = admin_client.get(reverse("kagi:webauthn-keys"))
    assert list(response.context_data["webauthnkey_list"]) == []
    assert response.status_code == 200


def test_add_webauthn_key(admin_client):
    response = admin_client.get(reverse("kagi:add-webauthn-key"))
    assert response.status_code == 200
    assert isinstance(response.context_data["form"], KeyRegistrationForm)


def test_totp_device_deletion_works(admin_client):
    user = User.objects.get(pk=1)
    key = user.webauthn_keys.create(key_name="SoloKey", sign_count=0)

    response = admin_client.get(reverse("kagi:webauthn-keys"))
    assert response.status_code == 200
    assert len(response.context_data["webauthnkey_list"]) == 1
    response = admin_client.post(
        reverse("kagi:webauthn-keys"), {"delete": "checked", "key_id": key.pk}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:webauthn-keys")
    assert WebAuthnKey.objects.count() == 0


# Testing view begin activate
def test_begin_activate_return_user_credential_options(admin_client):
    ukey = "Q3sM6zbLYAssRO7g5BM7"
    with mock.patch("kagi.views.api.util.generate_ukey", return_value=ukey):
        response = admin_client.post(
            reverse("kagi:begin-activate"), {"key_name": "SoloKey"}
        )
    assert response.status_code == 200
    credential_options = response.json()
    assert "challenge" in credential_options
    assert credential_options["rp"] == {
        "name": settings.RELYING_PARTY_NAME,
        "id": settings.RELYING_PARTY_ID,
    }
    assert credential_options["user"] == {
        "id": ukey,
        "name": "admin",
        "displayName": "",
        "icon": settings.WEBAUTHN_ICON_URL,
    }

    assert "pubKeyCredParams" in credential_options
    assert credential_options["extensions"] == {"webauthn.loc": True}


def test_begin_activate_fails_if_key_name_is_missing(admin_client):
    response = admin_client.post(reverse("kagi:begin-activate"), {"key_name": ""})
    assert response.status_code == 400
    assert response.json() == {"errors": {"key_name": ["This field is required."]}}


# Testing view verify credential info
def test_webauthn_verify_credential_info(admin_client):
    # Setup the session
    response = admin_client.post(
        reverse("kagi:begin-activate"), {"key_name": "SoloKey"}
    )
    credential_options = response.json()
    challenge = credential_options["challenge"]

    trusted_attestation_cert_required = (
        settings.WEBAUTHN_TRUSTED_ATTESTATION_CERT_REQUIRED
    )
    self_attestation_permitted = settings.WEBAUTHN_SELF_ATTESTATION_PERMITTED
    none_attestation_permitted = settings.WEBAUTHN_NONE_ATTESTATION_PERMITTED

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        webauthn_registration_response = (
            mocked_webauthn.WebAuthnRegistrationResponse.return_value
        )
        verify = webauthn_registration_response.verify.return_value
        verify.public_key.decode.return_value = "public-key"
        verify.credential_id.decode.return_value = "credential-id"
        verify.sign_count = 0

        response = admin_client.post(
            reverse("kagi:verify-credential-info"), {"registration": "payload"}
        )
    mocked_webauthn.WebAuthnRegistrationResponse.assert_called_with(
        settings.RELYING_PARTY_ID,
        "http://testserver",
        {"registration": ["payload"]},
        challenge,
        settings.WEBAUTHN_TRUSTED_CERTIFICATES,
        trusted_attestation_cert_required,
        self_attestation_permitted,
        none_attestation_permitted,
        uv_required=False,  # User validation
    )

    webauthn_registration_response.verify.assert_called_once()

    assert response.status_code == 200
    assert response.json() == {"success": "User successfully registered."}


def test_webauthn_verify_credential_info_fails_if_registration_is_invalid(admin_client):
    # Setup the session
    response = admin_client.post(
        reverse("kagi:begin-activate"), {"key_name": "SoloKey"}
    )

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        webauthn_registration_response = (
            mocked_webauthn.WebAuthnRegistrationResponse.return_value
        )
        verify = webauthn_registration_response.verify
        verify.side_effect = ValueError("An error occurred")

        response = admin_client.post(
            reverse("kagi:verify-credential-info"), {"registration": "payload"}
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Registration failed. Error: An error occurred"}


def test_webauthn_verify_credential_info_fails_if_credential_id_already_exists(
    admin_client
):
    # Setup the session
    response = admin_client.post(
        reverse("kagi:begin-activate"), {"key_name": "SoloKey"}
    )

    # Create the WebAuthnKey
    user = User.objects.get(pk=1)
    user.webauthn_keys.create(
        key_name="SoloKey", sign_count=0, credential_id="credential-id"
    )

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        webauthn_registration_response = (
            mocked_webauthn.WebAuthnRegistrationResponse.return_value
        )
        verify = webauthn_registration_response.verify.return_value
        verify.credential_id.decode.return_value = "credential-id"

        response = admin_client.post(
            reverse("kagi:verify-credential-info"), {"registration": "payload"}
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Credential ID already exists."}


# Testing view begin assertion
@pytest.mark.django_db
def test_begin_assertion_return_user_credential_options(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey 1",
        sign_count=0,
        credential_id="credential-id-1",
        ukey="abcd",
        public_key="pubkey1",
    )
    user.webauthn_keys.create(
        key_name="SoloKey 2",
        sign_count=0,
        credential_id="credential-id-2",
        ukey="efgh",
        public_key="pubkey2",
    )

    ukey = "Q3sM6zbLYAssRO7g5BM7"
    challenge = "k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    with mock.patch("kagi.views.api.util.generate_ukey", return_value=ukey):
        with mock.patch(
            "kagi.views.api.util.generate_challenge", return_value=challenge
        ):
            # We authenticate with username/password
            response = client.post(
                reverse("kagi:login"), {"username": "admin", "password": "admin"}
            )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        mocked_webauthn.WebAuthnAssertionOptions.side_effect = [
            mock.MagicMock(assertion_dict="solo-key-1"),
            mock.MagicMock(assertion_dict="solo-key-2"),
        ]
        response = client.post(reverse("kagi:begin-assertion"))

    assert response.status_code == 200
    assert response.json() == {"assertion_candidates": ["solo-key-1", "solo-key-2"]}


# Testing view verify assertion
@pytest.mark.django_db
def test_verify_assertion_validates_the_user_webauthn_key(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey",
        sign_count=0,
        credential_id="credential-id",
        ukey="abcd",
        public_key="pubkey",
    )
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    # We authenticate with username/password
    challenge = "k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    with mock.patch("kagi.views.api.util.generate_challenge", return_value=challenge):
        response = client.post(reverse("kagi:begin-assertion"))

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        webauthn_assertion_response = (
            mocked_webauthn.WebAuthnAssertionResponse.return_value
        )
        verify = webauthn_assertion_response.verify
        verify.return_value = 1

        response = client.post(
            reverse("kagi:verify-assertion"),
            {"id": "credential-id", "assertion": "payload"},
        )
    mocked_webauthn.WebAuthnUser.assert_called_with(
        "abcd",
        "admin",
        "",
        settings.WEBAUTHN_ICON_URL,
        "credential-id",
        "pubkey",
        0,
        settings.RELYING_PARTY_ID,
    )

    webauthn_user = mocked_webauthn.WebAuthnUser.return_value
    webauthn_assertion_response = mocked_webauthn.WebAuthnAssertionResponse
    webauthn_assertion_response.assert_called_with(
        webauthn_user,
        {"id": ["credential-id"], "assertion": ["payload"]},
        challenge,
        "http://testserver",
        uv_required=False,
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": "Successfully authenticated as admin",
        "redirect_to": reverse("kagi:two-factor-settings"),
    }

    # Are we truly logged in?
    response = client.get(reverse("kagi:two-factor-settings"))
    assert response.status_code == 200


# Testing view verify assertion
@pytest.mark.django_db
def test_verify_assertion_fails_if_missing_user_webauthn_key(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey",
        sign_count=0,
        credential_id="wrong-id",
        ukey="abcd",
        public_key="pubkey",
    )
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    # We authenticate with username/password
    challenge = "k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    with mock.patch("kagi.views.api.util.generate_challenge", return_value=challenge):
        response = client.post(reverse("kagi:begin-assertion"))

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        webauthn_assertion_response = (
            mocked_webauthn.WebAuthnAssertionResponse.return_value
        )
        verify = webauthn_assertion_response.verify
        verify.return_value = 1

        response = client.post(
            reverse("kagi:verify-assertion"),
            {"id": "credential-id", "assertion": "payload"},
        )
    assert response.status_code == 400
    assert response.json() == {"fail": "Key does not exist."}


@pytest.mark.django_db
def test_verify_assertion_validates_the_assertion(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey",
        sign_count=0,
        credential_id="credential-id",
        ukey="abcd",
        public_key="pubkey",
    )
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    # We authenticate with username/password
    challenge = "k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    response = client.get(reverse("kagi:verify-second-factor"))
    assert response.status_code == 200

    with mock.patch("kagi.views.api.util.generate_challenge", return_value=challenge):
        response = client.post(reverse("kagi:begin-assertion"))

    with mock.patch("kagi.views.api.webauthn") as mocked_webauthn:
        webauthn_assertion_response = (
            mocked_webauthn.WebAuthnAssertionResponse.return_value
        )
        verify = webauthn_assertion_response.verify
        verify.side_effect = ValueError("An error occurred")

        response = client.post(
            reverse("kagi:verify-assertion"),
            {"id": "credential-id", "assertion": "payload"},
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Assertion failed. Error: An error occurred"}
