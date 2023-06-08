CHANGELOG
=========

0.4.0 - 2023-06-08
------------------

* Add support for Python 3.11 and Django 4.2, by @MarkusH (#67).
 * "Pin" primary keys to `AutoField` so no new migrations are generated for now (#55).
 * Properly update `last_used_at` for FIDO tokens, by @MarkusH (#66).
 * Improve secret submission security when adding TOTP devices, by @MarkusH (#72).
 * Improve QR code display in Django Admin in dark mode, by @evanottinger (#75).
 * Publish Kagi via PyPI trusted publisher system, by @apollo13 (#74).

Contributed by [Florian Apolloner](https://github.com/apollo13) via [PR #76](https://github.com/justinmayer/kagi/pull/76/)


0.3.0 - 2022-09-18
------------------

* Update project for Django 4.1 compatibility
* Upgrade code for Python 3.7+ conventions

0.2.0 - 2021-11-05
------------------

- Add support for multiple WebAuthn keys (#4)
- Remove `django-extensions` and the need for HTTPS on localhost (#29)
- Many minor enhancements

0.1.0 - 2019-08-20
------------------

- Initial release
