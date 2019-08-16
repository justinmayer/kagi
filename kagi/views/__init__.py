from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from .backup_codes import BackupCodesView
from .login import KagiLoginView, VerifySecondFactorView
from .totp_devices import AddTOTPDeviceView, TOTPDeviceManagementView
from .webauthn_keys import AddWebAuthnKeyView, KeyManagementView


class TwoFactorSettingsView(TemplateView):
    template_name = "kagi/two_factor_settings.html"

    def get_context_data(self, **kwargs):
        context = super(TwoFactorSettingsView, self).get_context_data(**kwargs)
        context["webauthn_enabled"] = self.request.user.webauthn_keys.exists()
        context["backup_codes_count"] = self.request.user.backup_codes.count()
        context["totp_enabled"] = self.request.user.totp_devices.exists()
        return context


add_webauthn_key = AddWebAuthnKeyView.as_view()
verify_second_factor = VerifySecondFactorView.as_view()
login = KagiLoginView.as_view()
keys = login_required(KeyManagementView.as_view())
two_factor_settings = login_required(TwoFactorSettingsView.as_view())
backup_codes = login_required(BackupCodesView.as_view())
add_totp = login_required(AddTOTPDeviceView.as_view())
totp_devices = login_required(TOTPDeviceManagementView.as_view())
