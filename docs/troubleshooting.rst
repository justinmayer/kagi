Troubleshooting
###############

.. _troubleshooting:

We are doing the best we can so you do not have to read this section.

That said, we have included solutions (or at least explanations) for
some common problems below.

If you do not find a solution to your problem here, please
:ref:`ask for help <communication_channels>`!


socket.error: [Errno 48] Address already in use
===============================================

Another process has occupied django's default port 8000.

To fix this, see which service is running on port 8000::

$ sudo lsof -i :8000

and kill the process using PID from output::

$ kill -kill [PID]


DOMException / SecurityError: "The operation is insecure."
==========================================================

This means that the `navigator.credentials` Javascript API refused to start because:

- You are not connected on your website through HTTPS
- The certificate doesn't match the HOST.
- In development, maybe you are trying
  https://127.0.0.1:8000/kagi/login/ rather than
  https://localhost:8000/kagi/login/
