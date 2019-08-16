from datetime import datetime, date
import base64
import re

from django.urls import reverse
from django.utils import timezone

from ..models import TOTPDevice
from ..oath import totp

base32_regexp = re.compile(r'^(?:[A-Z2-7]{8})*(?:[A-Z2-7]{2}={6}|[A-Z2-7]{4}={4}|[A-Z2-7]{5}={3}|[A-Z2-7]{7}=)?$')


def test_list_totp_devices(admin_client):
    response = admin_client.get(reverse("kagi:totp-devices"))
    assert list(response.context_data["totpdevice_list"]) == []
    assert response.status_code == 200


def test_add_a_new_totp_device_shows_a_qrcode(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    assert response.context_data["qr_svg"].startswith('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<svg height="49mm" ')


def test_add_a_new_totp_device_context_data_contains_the_base32_key_and_otpauth_link(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    assert re.match(base32_regexp, response.context_data["base32_key"])
    assert response.context_data["otpauth"] == (
        f"otpauth://totp/testserver:admin?secret={response.context_data['base32_key']}"
        f"&digits=6&issuer=testserver"
    )


def test_add_a_new_totp_device_validates_the_otpauth_code_and_change_key_in_case_of_mismatch(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    base32_key = response.context_data["base32_key"]
    response = admin_client.post(
        reverse("kagi:add-totp"),
        {"base32_key": base32_key, "token": "123456"}
    )
    assert response.status_code == 200
    assert base32_key == response.context_data["base32_key"]
    form = response.context_data["form"]
    assert form.errors == {"token": ["That token is invalid."]}


def test_add_a_new_totp_device_validates_the_otpauth_code_and_create_the_device_if_valid(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    base32_key = response.context_data["base32_key"]

    now = timezone.now()
    key = base64.b32decode(base32_key.encode('utf-8'))
    token = totp(key, now)
    response = admin_client.post(
        reverse("kagi:add-totp"),
        {"base32_key": base32_key, "token": token}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:totp-devices")
    
    response = admin_client.get(reverse("kagi:totp-devices"))
    assert len(response.context_data["totpdevice_list"]) == 1


def test_prevent_reuse_of_totp_device_code(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    base32_key = response.context_data["base32_key"]

    now = timezone.now()
    key = base64.b32decode(base32_key.encode('utf-8'))
    token = totp(key, now)
    response = admin_client.post(
        reverse("kagi:add-totp"),
        {"base32_key": base32_key, "token": token}
    )
    assert response.status_code == 302
    device = TOTPDevice.objects.get()
    assert not device.validate_token(token)


def test_oath_handle_naive_datetime_objects(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    base32_key = response.context_data["base32_key"]

    now = datetime.now()
    key = base64.b32decode(base32_key.encode('utf-8'))
    token = totp(key, now)
    response = admin_client.post(
        reverse("kagi:add-totp"),
        {"base32_key": base32_key, "token": token}
    )
    assert response.status_code == 302
