from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.urls import reverse

import pytest

from ..models import BackupCode


def test_list_backup_codes(admin_client):
    response = admin_client.get(reverse("kagi:backup-codes"))
    assert list(response.context_data["backupcode_list"]) == []
    assert response.status_code == 200


def test_add_new_backup_codes(admin_client):
    response = admin_client.post(reverse("kagi:backup-codes"))
    assert response.status_code == 302
    response = admin_client.get(reverse("kagi:backup-codes"))
    assert len(response.context_data["backupcode_list"]) == 10


@pytest.mark.django_db
def test_addbackupcode_command():
    User.objects.create(username="admin", password="admin", email="john.doe@kagi.com")
    assert BackupCode.objects.count() == 0
    stdout = StringIO()
    call_command("addbackupcode", "admin", stdout=stdout)
    assert len(stdout.getvalue()) == 8
    assert BackupCode.objects.count() == 1


@pytest.mark.django_db
def test_addbackupcode_command_can_use_a_specific_code():
    User.objects.create(username="admin", password="admin", email="john.doe@kagi.com")
    assert BackupCode.objects.count() == 0
    call_command("addbackupcode", "admin", "--code", "123456", stdout=StringIO())
    assert BackupCode.objects.count() == 1


@pytest.mark.django_db
def test_addbackupcode_command_refuse_to_create_twice_the_same_code():
    User.objects.create(username="admin", password="admin", email="john.doe@kagi.com")
    assert BackupCode.objects.count() == 0
    call_command("addbackupcode", "admin", stdout=StringIO())
    code = BackupCode.objects.get().code
    with pytest.raises(CommandError):
        call_command("addbackupcode", "admin", "--code", code)


@pytest.mark.django_db
def test_backup_code_manager_handles_code_duplication():
    user = User.objects.create(
        username="admin", password="admin", email="john.doe@kagi.com"
    )
    assert BackupCode.objects.count() == 0
    with mock.patch(
        "kagi.models.get_random_string", side_effect=["123456", "123456", "45678"]
    ) as mocked:
        user.backup_codes.create_backup_code()
        user.backup_codes.create_backup_code()

    assert mocked.call_count == 3
    assert BackupCode.objects.count() == 2


@pytest.mark.django_db
def test_a_user_with_backup_codes_and_no_mfa_is_not_asked_for_its_code(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.backup_codes.create_backup_code()
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:two-factor-settings")

    # Are we truly logged in?
    response = client.get(reverse("kagi:two-factor-settings"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_a_user_with_mfa_can_use_a_backup_code(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.totp_devices.create()
    user.backup_codes.create_backup_code(code="123456")
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    response = client.post(
        reverse("kagi:verify-second-factor"), {"type": "backup", "code": "123456"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:two-factor-settings")

    # Check that the used code has been removed.
    assert BackupCode.objects.count() == 0

    # Are we truly logged in?
    response = client.get(reverse("kagi:two-factor-settings"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_a_user_cannot_login_with_a_wrong_backup_code(client):
    # We need to create a couple of WebAuthnKey for our user.
    user = User.objects.create_user("admin", "john.doe@kagi.com", "admin")
    user.totp_devices.create()
    user.backup_codes.create_backup_code(code="123456")
    response = client.post(
        reverse("kagi:login"), {"username": "admin", "password": "admin"}
    )
    assert response.status_code == 302
    assert response.url == reverse("kagi:verify-second-factor")

    response = client.post(
        reverse("kagi:verify-second-factor"), {"type": "backup", "code": "213456"}
    )
    assert response.status_code == 200
    assert response.context_data["forms"]["backup"].errors == {
        "code": ["That is not a valid backup code."]
    }
