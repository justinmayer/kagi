from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class SecondFactorForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.request = kwargs.pop("request")
        self.appId = kwargs.pop("appId")
        return super(SecondFactorForm, self).__init__(*args, **kwargs)


class BackupCodeForm(SecondFactorForm):
    INVALID_ERROR_MESSAGE = _("That is not a valid backup code.")

    code = forms.CharField(
        label=_("Code"), widget=forms.TextInput(attrs={"autocomplete": "off"})
    )

    def validate_second_factor(self):
        count, _ = self.user.backup_codes.filter(
            code=self.cleaned_data["code"]
        ).delete()
        if count == 0:
            self.add_error("code", self.INVALID_ERROR_MESSAGE)
            return False
        elif count == 1:
            return True


class TOTPForm(SecondFactorForm):
    INVALID_ERROR_MESSAGE = _("That token is invalid.")

    token = forms.CharField(
        min_length=6,
        max_length=6,
        label=_("Token"),
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
    )

    def validate_second_factor(self):
        for device in self.user.totp_devices.all():
            if device.validate_token(self.cleaned_data["token"]):
                device.last_used_at = timezone.now()
                device.save()
                return True
        self.add_error("token", self.INVALID_ERROR_MESSAGE)
        return False


class KeyRegistrationForm(forms.Form):
    key_name = forms.CharField(label=_("Key name"))
