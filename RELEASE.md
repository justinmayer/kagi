Release type: minor

 * Add support for Python 3.11 and Django 4.2, by @MarkusH (#67).
 * "Pin" primary keys to `AutoField` so no new migrations are generated for now (#55).
 * Properly update `last_used_at` for FIDO tokens, by @MarkusH (#66).
 * Improve secret submission security when adding TOTP devices, by @MarkusH (#72).
 * Improve QR code display in Django Admin in dark mode, by @evanottinger (#75).
 * Publish Kagi via PyPI trusted publisher system, by @apollo13 (#74).
