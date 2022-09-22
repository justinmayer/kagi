import json
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse

import pytest
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
