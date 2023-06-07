Release type: minor

 * Added support for Python 3.11 and Django 4.2
 * "Pin" primary keys to `AutoField` so no new migrations are generated for now (#55).
 * Properly update `last_used_at` for Fido tokens (#48, #56).
