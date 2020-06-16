Kagi
====

|coc| |circleci| |pypi| |readthedocs|


.. |coc| image:: https://img.shields.io/badge/%E2%9D%A4-code%20of%20conduct-blue.svg
    :target: https://github.com/justinmayer/kagi/blob/master/CODE_OF_CONDUCT.rst
    :alt: Code of Conduct

.. |circleci| image:: https://img.shields.io/circleci/build/github/justinmayer/kagi
    :target: https://circleci.com/gh/justinmayer/kagi
    :alt: Build Status

.. |coverage| image:: https://img.shields.io/badge/coverage-100%25-brightgreen
    :alt: Code Coverage

.. |readthedocs| image:: https://readthedocs.org/projects/kagi/badge/?version=latest
    :target: https://kagi.readthedocs.io/en/latest/
    :alt: Documentation Status

.. |pypi| image:: https://img.shields.io/pypi/v/kagi.svg
    :target: https://pypi.python.org/pypi/kagi
    :alt: PyPI Version


Kagi provides support for FIDO WebAuthn security keys and TOTP tokens in Django.

Kagi is a relatively young project and has not yet been fully battle-tested.
Its use in a high-impact environment should be accompanied by a thorough
understanding of how it works before relying on it.

Installation
------------

::

    pip install kagi

Add ``kagi`` to ``INSTALLED_APPS`` and include ``kagi.urls`` somewhere in your
URL patterns. Set: ``LOGIN_URL = "kagi:login"``

Make sure that Django’s built-in login view does not have a
``urlpattern``, because it will authenticate users without their second
factor. Kagi provides its own login view to handle that.

Demo
----

To see a demo, use the test project included in this repository and perform the
following steps (creating and activating a virtual environment first is optional).

First, install Poetry_::

   curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

Clone the Kagi source code and switch to its directory::

   git clone https://github.com/justinmayer/kagi.git && cd kagi

Install dependencies, run database migrations, create a user, and serve the demo::

   poetry install
   invoke migrate
   python testproj/manage.py createsuperuser
   invoke serve

You should now be able to see the demo project login page in your browser at:
http://localhost:8000/kagi/login

Supported browsers and versions can be found here: https://caniuse.com/webauthn
For domains other than ``localhost``, WebAuthn requires that the site is served
over a secure (HTTPS) connection.

Since you haven’t added any security keys yet, you will be logged in with just a
username and password. Once logged in and on the multi-factor settings page,
choose “Manage WebAuthn keys” and then “Add another key” and follow the provided
instructions. Once WebAuthn and/or TOTP has been successfully configured, your
account will be protected by multi-factor authentication, and when you log in
the next time, your WebAuthn key or TOTP token will be required.

You can manage the keys attached to your account on the key management page at:
http://localhost:8000/kagi/keys


Using WebAuthn Keys on Linux
============================

Some distros don’t come with udev rules to make USB HID /dev/
nodes accessible to normal users. If your key doesn’t light up
and start flashing when you expect it to, this might be what is
happening. See https://github.com/Yubico/libu2f-host/issues/2 and
https://github.com/Yubico/libu2f-host/blob/master/70-u2f.rules for some
discussion of the rule to make it accessible. If you just want a quick
temporary fix, you can run ``sudo chmod 666 /dev/hidraw*`` every time
after you plug in your key (the files disappear after unplugging).

.. _Poetry: https://poetry.eustace.io/docs/#installation
