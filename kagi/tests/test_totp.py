import base64
from datetime import datetime
import re

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

import pytest

from ..models import TOTPDevice
from ..oath import totp

base32_regexp = re.compile(
    r"^(?:[A-Z2-7]{8})*(?:[A-Z2-7]{2}={6}|[A-Z2-7]{4}={4}|[A-Z2-7]{5}={3}|[A-Z2-7]{7}=)?$"
)


def add_new_totp_device(client, *, url=None, now=None):
    if url is None:
        url = reverse("kagi:add-totp")

    if now is None:
        now = timezone.now()

    response = client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200

    base32_key = response.context_data["base32_key"]
    key = base64.b32decode(base32_key.encode("utf-8"))
    token = totp(key, now)
    response = client.post(url, {"base32_key": base32_key, "token": token})
    response.token = token
    return response


def test_list_totp_devices(admin_client):
    response = admin_client.get(reverse("kagi:totp-devices"))
    assert list(response.context_data["totpdevice_list"]) == []
    assert response.status_code == 200


def test_add_a_new_totp_device_shows_a_qrcode(admin_client):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    assert response.context_data["qr_svg"].startswith(
        "<?xml version='1.0' encoding='UTF-8'?>\n<svg height=\"49mm\" "
    )


def test_add_a_new_totp_device_context_data_contains_the_base32_key_and_otpauth_link(
    admin_client
):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    assert re.match(base32_regexp, response.context_data["base32_key"])
    assert response.context_data["otpauth"] == (
        f"otpauth://totp/testserver:admin?secret={response.context_data['base32_key']}"
        f"&digits=6&issuer=testserver"
    )


def test_add_a_new_totp_device_validates_the_otpauth_code_and_change_key_in_case_of_mismatch(
    admin_client
):
    response = admin_client.get(reverse("kagi:add-totp"))
    assert response.status_code == 200
    base32_key = response.context_data["base32_key"]
    response = admin_client.post(
        reverse("kagi:add-totp"), {"base32_key": base32_key, "token": "123456"}
    )
    assert response.status_code == 200
    assert base32_key == response.context_data["base32_key"]
    form = response.context_data["form"]
    assert form.errors == {"token": ["That token is invalid."]}


def test_add_a_new_totp_device_validates_the_otpauth_code_and_create_the_device_if_valid(
    admin_client
):
    response = add_new_totp_device(admin_client)
    assert response.status_code == 302
    assert response.url == reverse("kagi:totp-devices")

    response = admin_client.get(reverse("kagi:totp-devices"))
    assert len(response.context_data["totpdevice_list"]) == 1


def test_prevent_reuse_of_totp_device_code(admin_client):
    response = add_new_totp_device(admin_client)
    assert response.status_code == 302
    device = TOTPDevice.objects.get()
    assert not device.validate_token(response.token)


def test_oath_handle_naive_datetime_objects(admin_client):
    response = add_new_totp_device(admin_client, now=datetime.now())
    assert response.status_code == 302


def test_add_a_new_totp_device_redirects_to_the_next_parameter(admin_client):
    url = reverse("kagi:add-totp")
    next_url = reverse("kagi:two-factor-settings")

    response = add_new_totp_device(admin_client, url=f"{url}?next={next_url}")
    assert response.status_code == 302
    assert response.url == next_url


def test_totp_device_deletion_works(admin_client):
    add_new_totp_device(admin_client)
    device = TOTPDevice.objects.get()

    response = admin_client.post(
        reverse("kagi:totp-devices"), {"delete": "checked", "device_id": device.pk}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:totp-devices")
    assert TOTPDevice.objects.count() == 0


@pytest.mark.django_db
def test_a_user_can_confirm_login_with_its_totp_device(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    key = base64.b32decode("7AQ6YRY4OEL7IEHQ6FUWSBRX6W4ZYURF")
    user.totp_devices.create(key=key)
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    now = timezone.now()
    token = totp(key, now)
    response = client.post(
        reverse("kagi:verify-second-factor"), {"type": "totp", "token": token}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:two-factor-settings")

    # Are we truly logged in?
    response = client.get(reverse("kagi:two-factor-settings"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_a_user_cannot_confirm_login_with_a_wrong_token(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    key = base64.b32decode("7AQ6YRY4OEL7IEHQ6FUWSBRX6W4ZYURF")
    user.totp_devices.create(key=key)
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    response = client.post(
        reverse("kagi:verify-second-factor"), {"type": "totp", "token": "123456"}
    )
    assert response.status_code == 200
    assert response.context_data["forms"]["totp"].errors == {
        "token": ["That token is invalid."]
    }


@pytest.mark.django_db
def test_a_user_can_be_redirected_to_the_next_parameter(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    key = base64.b32decode("7AQ6YRY4OEL7IEHQ6FUWSBRX6W4ZYURF")
    user.totp_devices.create(key=key)
    url = reverse("kagi:login")
    next_url = reverse("kagi:add-webauthn-key")

    response = client.post(
        f"{url}?next={next_url}", {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    url = reverse("kagi:verify-second-factor")
    verify_url = f"{url}?next=%2Fkagi%2Fadd-webauthn-key%2F"
    assert response.url == verify_url

    now = timezone.now()
    token = totp(key, now)
    response = client.post(verify_url, {"type": "totp", "token": token})
    assert response.status_code == 302
    assert response.url == reverse("kagi:add-webauthn-key")


@pytest.mark.django_db
def test_an_admin_user_shows_the_admin_base_style(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.is_staff = True
    user.is_superuser = True
    user.save()
    key = base64.b32decode("7AQ6YRY4OEL7IEHQ6FUWSBRX6W4ZYURF")
    user.totp_devices.create(key=key)
    url = reverse("admin:login")
    next_url = reverse("kagi:add-webauthn-key")

    response = client.post(
        f"{url}?next={next_url}", {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    url = reverse("kagi:verify-second-factor")
    verify_url = f"{url}?next=%2Fkagi%2Fadd-webauthn-key%2F&admin=1"
    assert response.url == verify_url

    response = client.get(verify_url)
    assert response.status_code == 200

    now = timezone.now()
    token = totp(key, now)
    response = client.post(verify_url, {"type": "totp", "token": token})
    assert response.status_code == 302
    assert response.url == reverse("kagi:add-webauthn-key")


@pytest.mark.django_db
def test_in_case_the_session_expires_redirect_to_login(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    key = base64.b32decode("7AQ6YRY4OEL7IEHQ6FUWSBRX6W4ZYURF")
    user.totp_devices.create(key=key)
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    client.session.flush()
    response = client.get(reverse("kagi:verify-second-factor"))
    assert response.status_code == 302
    assert response.url == reverse("kagi:login")
