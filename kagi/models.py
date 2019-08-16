import datetime
import hmac
import string

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from .oath import T, totp


class WebAuthnKey(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="webauthn_keys", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True)

    key_name = models.CharField(max_length=64)
    public_key = models.TextField(unique=True)
    ukey = models.TextField(unique=True)
    credential_id = models.TextField(unique=True)
    sign_count = models.IntegerField()


class BackupCodeManager(models.Manager):
    def create_backup_code(self, code=None):
        if code is not None:
            return self.create(code=code)

        while True:
            try:
                with transaction.atomic():
                    code = get_random_string(length=6, allowed_chars=string.digits)
                    return self.create(code=code)
            except IntegrityError:
                pass


class BackupCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="backup_codes", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=8)

    class Meta:
        unique_together = [("user", "code")]

    objects = BackupCodeManager()


class TOTPDevice(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="totp_devices", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True)

    key = models.BinaryField()
    # the T value of the most recently-used token. This prevents using the same
    # token twice.
    last_t = models.PositiveIntegerField(null=True)

    def validate_token(self, token):
        step = datetime.timedelta(seconds=30)
        now = timezone.now()
        # the number of time intervals on either side to check
        slop = 1

        times_to_check = [now + i * step for i in range(-slop, slop + 1)]
        # prevent using the same token twice
        if self.last_t is not None:
            times_to_check = [t for t in times_to_check if T(t) > self.last_t]

        token = str(token)
        for t in times_to_check:
            if hmac.compare_digest(totp(self.key, t), token):
                self.last_t = T(t)
                return True
        return False
