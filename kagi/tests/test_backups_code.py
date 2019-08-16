import pytest
from unittest import mock

from django.core.management import call_command, CommandError
from django.contrib.auth.models import User
from django.urls import reverse

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
    call_command("addbackupcode", "admin")
    assert BackupCode.objects.count() == 1


@pytest.mark.django_db
def test_addbackupcode_command_can_use_a_specific_code():
    User.objects.create(username="admin", password="admin", email="john.doe@kagi.com")
    assert BackupCode.objects.count() == 0
    call_command("addbackupcode", "admin", "--code", "123456")
    assert BackupCode.objects.count() == 1


@pytest.mark.django_db
def test_addbackupcode_command_refuse_to_create_twice_the_same_code():
    User.objects.create(username="admin", password="admin", email="john.doe@kagi.com")
    assert BackupCode.objects.count() == 0
    call_command("addbackupcode", "admin")
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
