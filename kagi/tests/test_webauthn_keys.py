import json
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse

import pytest
from kagi.utils import webauthn
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import AttestationFormat, PublicKeyCredentialType
from webauthn.registration.verify_registration_response import VerifiedRegistration

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
        "id": bytes_to_base64url(b"1"),
        "name": "admin",
        "displayName": "admin",
    }

    assert "pubKeyCredParams" in credential_options


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
    with mock.patch("kagi.views.api.webauthn.verify_registration_response", return_value = fake_validated_credential) as mocked_verify_registration_response:
        response = admin_client.post(
            reverse("kagi:verify-credential-info"), {"credentials": "fake_payload"}
        )

    assert mocked_verify_registration_response.called_once

    assert response.status_code == 200
    assert response.json() == {"success": "User successfully registered."}


def test_webauthn_verify_credential_info_fails_if_registration_is_invalid(admin_client):
    # Setup the session
    response = admin_client.post(
        reverse("kagi:begin-activate"), {"key_name": "SoloKey"}
    )

    with mock.patch("kagi.views.api.webauthn.verify_registration_response") as mocked_verify_registration_response:
        mocked_verify_registration_response.side_effect = webauthn.RegistrationRejectedError("An error occurred")

        response = admin_client.post(
            reverse("kagi:verify-credential-info"), {"credentials": "payload"}
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Registration failed. Error: An error occurred"}


def test_webauthn_verify_credential_info_fails_if_credential_id_already_exists(
    admin_client,
):
    # Setup the session
    response = admin_client.post(
        reverse("kagi:begin-activate"), {"key_name": "SoloKey"}
    )

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
    with mock.patch("kagi.views.api.webauthn.verify_registration_response", return_value = fake_validated_credential) as mocked_verify_registration_response:
        response = admin_client.post(
            reverse("kagi:verify-credential-info"), {"credentials": "fake_payload"}
        )

    assert response.status_code == 400
    assert response.json() == {"fail": "Credential ID already exists."}
