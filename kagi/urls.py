from django.urls import path

from . import views
from .views import api

app_name = "kagi"

urlpatterns = [
    path(
        "verify-second-factor/",
        views.verify_second_factor,
        name="verify-second-factor",
    ),
    path("login/", views.login, name="login"),
    path("keys/", views.keys, name="webauthn-keys"),
    path("add-webauthn-key/", views.add_webauthn_key, name="add-webauthn-key"),
    path("two-factor-settings/", views.two_factor_settings, name="two-factor-settings"),
    path("backup-codes/", views.backup_codes, name="backup-codes"),
    path("add-totp-device/", views.add_totp, name="add-totp"),
    path("totp-devices/", views.totp_devices, name="totp-devices"),
    path("api/begin-activate/", api.webauthn_begin_activate, name="begin-activate"),
    path(
        "api/verify-credential-info/",
        api.webauthn_verify_credential_info,
        name="verify-credential-info",
    ),
    path("api/begin-assertion/", api.webauthn_begin_assertion, name="begin-assertion"),
    path(
        "api/verify-assertion/",
        api.webauthn_verify_assertion,
        name="verify-assertion",
    ),
]
