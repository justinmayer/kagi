Customization
#############

Handling Unsupported Browsers
=============================

The provided ``webauthn.js`` file detects whether browsers support WebAuthn, and
if not, displays or hides selected element IDs as appropriate. There are matching
element IDs in the bundled templates, which can be useful as a guide for how to
handle this in customized templates.

Elements with ID ``webauthn-feature`` will be set to ``style="display: none"``.
This is for hiding functional elements that require WebAuthn support, since using
those elements in an unsupported browser would only result in errors.

Elements with ID ``webauthn-undefined-error`` will be set to ``style="display: block"``.
This is useful for displaying a warning in unsupported browsers, along with a link
to a list of compatible browsers.
