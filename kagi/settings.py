import os.path

from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


RELYING_PARTY_ID = getattr(settings, "RELYING_PARTY_ID", "localhost")
RELYING_PARTY_NAME = getattr(settings, "RELYING_PARTY_NAME", "Kagi Test Project")
WEBAUTHN_ICON_URL = getattr(settings, "WEBAUTHN_ICON_URL", None)
WEBAUTHN_TRUSTED_CERTIFICATES = getattr(
    settings,
    "WEBAUTHN_TRUSTED_CERTIFICATES",
    os.path.join(BASE_DIR, "..", "trusted_attestation_roots"),
)
WEBAUTHN_TRUSTED_ATTESTATION_CERT_REQUIRED = getattr(
    settings, "WEBAUTHN_TRUSTED_ATTESTATION_CERT_REQUIRED", False
)
WEBAUTHN_SELF_ATTESTATION_PERMITTED = getattr(
    settings, "WEBAUTHN_SELF_ATTESTATION_PERMITTED", False
)
WEBAUTHN_NONE_ATTESTATION_PERMITTED = getattr(
    settings, "WEBAUTHN_NONE_ATTESTATION_PERMITTED", False
)
