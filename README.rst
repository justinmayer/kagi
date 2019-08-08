Kagi
----

.. image:: https://travis-ci.org/justinmayer/kagi.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/justinmayer/kagi

kagi provides support for FIDO U2F security tokens in Django.

The functionality is similar to the `Security Key two-factor authentication that Google recently announced <http://googleonlinesecurity.blogspot.com/2014/10/strengthening-2-step-verification-with.html>`_,
and uses the same tokens.

kagi isn't yet production ready, but is a working proof of
concept. There are many TODOs sprinkled around the code that should be
fixed before relying on it.

It is based on django_u2f and aims to support fifo2 API.

Installation
============

::

    $ pip install kagi

Add ``kagi`` to ``INSTALLED_APPS`` and include ``kagi.urls`` somewhere in your url patterns.
Set ``LOGIN_URL = 'u2f:login'``.

Make sure that Django's built-in login view does not have a
urlpattern, because it will authenticate users without their second
factor. kagi provides its own login view to handle that.

Demo
====

To see a demo, use the test project included in the repo and perform the 
following steps (using virtualenv is optional)::

   git clone https://github.com/justinmayer/kagi
   cd kagi
   virtualenv -p python3 venv
   source venv/bin/activate
   pip install -e .
   cd testproj
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runssserver

Look at supported browser version there: https://caniuse.com/webauthn
U2F also requires that the page is served over a secure connection.

Start by going to https://localhost:8000/kagi/login. Since you
haven't added any security keys yet, you will be logged in with just a
username and password.

Once logged in, click 'Add another key' on the key management page and
follow the instructions. Now your account is protected by two factor
authentication, and when you log in again your U2F token will be
required.

You can administrate the keys attached to your account on the key
management page as well, at the URL https://localhost:8000/kagi/keys.


Using U2F keys on linux
=======================

Some distros don't come with udev rules to make USB HID /dev/
nodes accessible to normal users. If your key doesn't light up
and start flashing when you expect it to, this might be what is
happening. See https://github.com/Yubico/libu2f-host/issues/2 and
https://github.com/Yubico/libu2f-host/blob/master/70-u2f.rules for some
discussion of the rule to make it accessible. If you just want a quick
temporary fix, you can run ``sudo chmod 666 /dev/hidraw*`` every time
after you plug in your key (The files disappear after unplugging).


Helpful links
=============

- The code to actually implement the crypto in python:
  https://github.com/Yubico/python-u2flib-server
- A description of the process from a developer's perspective from Yubico:
  https://developers.yubico.com/U2F/Libraries/Using_a_library.html
