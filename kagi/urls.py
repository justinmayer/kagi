from django.conf.urls import url

from . import views
from .views import api

app_name = "kagi"

urlpatterns = [
    url(
        r"^verify-second-factor/",
        views.verify_second_factor,
        name="verify-second-factor",
    ),
    url(r"^login/", views.login, name="login"),
    url(r"^keys/", views.keys, name="webauthn-keys"),
    url(r"^add-webauthn-key/", views.add_webauthn_key, name="add-webauthn-key"),
    url(
        r"^two-factor-settings/", views.two_factor_settings, name="two-factor-settings"
    ),
    url(r"^backup-codes/", views.backup_codes, name="backup-codes"),
    url(r"^add-totp-device/", views.add_totp, name="add-totp"),
    url(r"^totp-devices/", views.totp_devices, name="totp-devices"),
    url(r"^api/begin-activate/", api.webauthn_begin_activate, name="begin-activate"),
    url(
        r"^api/verify-credential-info/",
        api.webauthn_verify_credential_info,
        name="verify-credential-info",
    ),
    url(r"^api/begin-assertion/", api.webauthn_begin_assertion, name="begin-assertion"),
    url(
        r"^api/verify-assertion/",
        api.webauthn_verify_assertion,
        name="verify-assertion",
    ),
]
