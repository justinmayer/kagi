import json
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse

import pytest
from webauthn.authentication.verify_authentication_response import (
    VerifiedAuthentication,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    AttestationFormat,
    AuthenticationCredential,
    AuthenticatorAssertionResponse,
    PublicKeyCredentialType,
)
from webauthn.registration.verify_registration_response import VerifiedRegistration

from kagi.utils import webauthn

from .. import settings
from ..forms import KeyRegistrationForm
from ..models import WebAuthnKey


def test_list_webauthn_keys(admin_client):
    response = admin_client.get(reverse("kagi:webauthn-keys"))
    assert list(response.context_data["webauthnkey_list"]) == []
    assert response.status_code == 200


def test_webauthn_keys_str_return_the_username(admin_client):
    user = User.objects.get(pk=1)
    key = user.webauthn_keys.create(key_name="SoloKey", sign_count=0)
    assert str(key) == "admin - SoloKey"


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
    response = admin_client.get(reverse("kagi:begin-activate"))

    assert response.status_code == 200
    credential_options = response.json()
    assert "challenge" in credential_options
    assert credential_options["rp"] == {
        "name": settings.RELYING_PARTY_NAME,
        "id": settings.RELYING_PARTY_ID,
    }
    assert credential_options["user"] == {
        "id": bytes_to_base64url(b"1"),
        "name": "admin",
        "displayName": "admin",
    }

    assert "pubKeyCredParams" in credential_options


# Testing view verify credential info
def test_webauthn_verify_credential_info(admin_client):
    # Setup the session
    response = admin_client.get(reverse("kagi:begin-activate"))

    fake_validated_credential = VerifiedRegistration(
        credential_id=b"foo",
        credential_public_key=b"bar",
        sign_count=0,
        aaguid="wutang",
        fmt=AttestationFormat.NONE,
        credential_type=PublicKeyCredentialType.PUBLIC_KEY,
        user_verified=False,
        attestation_object=b"foobar",
        credential_device_type="single_device",
        credential_backed_up=False,
    )
    with mock.patch(
        "kagi.views.api.webauthn.verify_registration_response",
        return_value=fake_validated_credential,
    ) as mocked_verify_registration_response:
        response = admin_client.post(
            reverse("kagi:verify-credential-info"),
            {"credentials": "fake_payload", "key_name": "SoloKey"},
        )

    assert mocked_verify_registration_response.called_once

    assert response.status_code == 200
    assert response.json() == {"success": "User successfully registered."}


def test_webauthn_verify_credential_info_fails_if_registration_is_invalid(admin_client):
    # Setup the session
    response = admin_client.get(reverse("kagi:begin-activate"))

    with mock.patch(
        "kagi.views.api.webauthn.verify_registration_response"
    ) as mocked_verify_registration_response:
        mocked_verify_registration_response.side_effect = (
            webauthn.RegistrationRejectedError("An error occurred")
        )

        response = admin_client.post(
            reverse("kagi:verify-credential-info"),
            {"credentials": "payload", "key_name": "SoloKey"},
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Registration failed. Error: An error occurred"}


def test_webauthn_verify_credential_info_fails_if_credential_id_already_exists(
    admin_client,
):
    # Setup the session
    response = admin_client.get(reverse("kagi:begin-activate"))

    # Create the WebAuthnKey
    user = User.objects.get(pk=1)
    user.webauthn_keys.create(
        key_name="SoloKey", sign_count=0, credential_id=bytes_to_base64url(b"foo")
    )

    fake_validated_credential = VerifiedRegistration(
        credential_id=b"foo",
        credential_public_key=b"bar",
        sign_count=0,
        aaguid="wutang",
        fmt=AttestationFormat.NONE,
        credential_type=PublicKeyCredentialType.PUBLIC_KEY,
        user_verified=False,
        attestation_object=b"foobar",
        credential_device_type="single_device",
        credential_backed_up=False,
    )
    with mock.patch(
        "kagi.views.api.webauthn.verify_registration_response",
        return_value=fake_validated_credential,
    ):
        response = admin_client.post(
            reverse("kagi:verify-credential-info"),
            {"credentials": "fake_payload", "key_name": "Solo key"},
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Credential ID already exists."}


def test_webauthn_verify_credential_info_fails_if_key_name_is_missing(
    admin_client,
):
    # Setup the session
    response = admin_client.get(reverse("kagi:begin-activate"))

    response = admin_client.post(
        reverse("kagi:verify-credential-info"), {"credentials": "fake_payload"}
    )

    assert response.status_code == 400
    assert response.json() == {"errors": {"key_name": ["This field is required."]}}


# Testing view begin assertion
@pytest.mark.django_db
def test_begin_assertion_return_user_credential_options(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey 1",
        sign_count=0,
        credential_id=bytes_to_base64url(b"credential-id-1"),
        public_key=bytes_to_base64url(b"pubkey1"),
    )
    user.webauthn_keys.create(
        key_name="SoloKey 2",
        sign_count=0,
        credential_id=bytes_to_base64url(b"credential-id-2"),
        public_key=bytes_to_base64url(b"pubkey2"),
    )

    challenge = b"k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    assertion_dict = {
        "challenge": bytes_to_base64url(challenge),
        "timeout": 60000,
        "rpId": "localhost",
        "allowCredentials": [
            {
                "id": bytes_to_base64url(b"credential-id-1"),
                "type": "public-key",
                "transports": ["usb", "nfc", "ble", "internal"],
            },
            {
                "id": bytes_to_base64url(b"credential-id-2"),
                "type": "public-key",
                "transports": ["usb", "nfc", "ble", "internal"],
            },
        ],
        "userVerification": "discouraged",
    }

    # We authenticate with username/password
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    with mock.patch(
        "kagi.views.api.webauthn.generate_webauthn_challenge", return_value=challenge
    ):
        response = client.get(reverse("kagi:begin-assertion"))

    assert response.status_code == 200
    assert response.json() == assertion_dict


# Testing view verify assertion
@pytest.mark.django_db
def test_verify_assertion_validates_the_user_webauthn_key(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey",
        sign_count=0,
        credential_id=bytes_to_base64url(b"credential-id"),
        public_key=bytes_to_base64url(b"pubkey"),
    )
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    response = client.get(reverse("kagi:verify-second-factor"))
    assert response.status_code == 200

    # We authenticate with username/password
    challenge = b"k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    with mock.patch(
        "kagi.views.api.webauthn.generate_webauthn_challenge", return_value=challenge
    ):
        response = client.get(reverse("kagi:begin-assertion"))

    fake_verified_authentication = VerifiedAuthentication(
        credential_id=b"credential-id",
        new_sign_count=69,
        credential_device_type="single_device",
        credential_backed_up=False,
    )
    with mock.patch(
        "kagi.views.api.webauthn.verify_assertion_response",
        return_value=fake_verified_authentication,
    ):

        response = client.post(
            reverse("kagi:verify-assertion"),
            {"credentials": json.dumps({"fake": "payload"})},
        )

    assert response.status_code == 200
    assert response.json() == {
        "success": "Successfully authenticated as admin",
        "redirect_to": reverse("kagi:two-factor-settings"),
    }


@pytest.mark.django_db
def test_verify_assertion_validates_the_assertion(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.webauthn_keys.create(
        key_name="SoloKey",
        sign_count=0,
        credential_id=bytes_to_base64url(b"credential-id"),
        public_key=bytes_to_base64url(b"pubkey"),
    )
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    # We authenticate with username/password
    challenge = b"k31d65xGDFb0VUq4MEMXmWpuWkzPs889"

    with mock.patch(
        "kagi.views.api.webauthn.generate_webauthn_challenge", return_value=challenge
    ):
        response = client.get(reverse("kagi:begin-assertion"))

    with mock.patch(
        "kagi.views.api.webauthn.AuthenticationCredential.parse_raw",
        return_value=AuthenticationCredential(
            id="foo",
            raw_id=b"~\x8a",
            response=AuthenticatorAssertionResponse(
                client_data_json=b'{"type": "webauthn.get", "challenge": "", "origin": "localhost"}',
                authenticator_data=b"~\x8a",
                signature=b"\xc2\xebZ\x9e",
                user_handle=None,
            ),
            type=PublicKeyCredentialType.PUBLIC_KEY,
        ),
    ):
        response = client.post(
            reverse("kagi:verify-assertion"),
            {"credentials": json.dumps({"fake": "payload"})},
        )

    assert response.status_code == 400
    assert response.json() == {
        "fail": "Assertion failed. Error: Invalid WebAuthn credential"
    }
