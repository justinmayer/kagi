import random
import string

from django.conf import settings
from django.contrib.auth import load_backend


def get_origin(request):
    return f"{request.scheme}://{request.get_host()}"


def get_user(request):
    try:
        user_id = request.session["kagi_pre_verify_user_pk"]
        backend_path = request.session["kagi_pre_verify_user_backend"]
        assert backend_path in settings.AUTHENTICATION_BACKENDS
        backend = load_backend(backend_path)
        user = backend.get_user(user_id)
        if user is not None:
            user.backend = backend_path
        return user
    except (KeyError, AssertionError):  # pragma: no cover
        return None
