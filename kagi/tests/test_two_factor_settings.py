from django.contrib.auth.models import User
from django.urls import reverse


def test_mfa_settings_page_displays_mfa_statuses(admin_client):
    response = admin_client.get(reverse("kagi:two-factor-settings"))

    assert response.context_data["webauthn_enabled"] is False
    assert response.context_data["totp_enabled"] is False
    assert response.context_data["backup_codes_count"] == 0


def test_mfa_settings_page_knows_when_webauthn_is_enabled(admin_client):
    user = User.objects.get(pk=1)

    user.webauthn_keys.create(key_name="SoloKey", sign_count=0)
    response = admin_client.get(reverse("kagi:two-factor-settings"))

    assert response.context_data["webauthn_enabled"] is True
    assert response.context_data["totp_enabled"] is False
    assert response.context_data["backup_codes_count"] == 0


def test_mfa_settings_page_knows_when_totp_is_enabled(admin_client):
    user = User.objects.get(pk=1)

    user.totp_devices.create()
    response = admin_client.get(reverse("kagi:two-factor-settings"))

    assert response.context_data["webauthn_enabled"] is False
    assert response.context_data["totp_enabled"] is True
    assert response.context_data["backup_codes_count"] == 0


def test_mfa_settings_page_knows_how_to_count_backup_codes(admin_client):
    user = User.objects.get(pk=1)

    user.backup_codes.create_backup_code()
    response = admin_client.get(reverse("kagi:two-factor-settings"))

    assert response.context_data["webauthn_enabled"] is False
    assert response.context_data["totp_enabled"] is False
    assert response.context_data["backup_codes_count"] == 1
