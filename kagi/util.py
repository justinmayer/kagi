import random
import string

from django.conf import settings
from django.contrib.auth import load_backend


def generate_challenge(challenge_len):
    return "".join(
        [
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for i in range(challenge_len)
        ]
    )


def generate_ukey():
    """Its value's ID member is required, and contains an identifier
    for the account, specified by the Relying Party. This is not meant
    to be displayed to the user, but is used by the Relying Party to
    control the number of credentials -- an authenticator will never
    contain more than one credential for a given Relying Party under
    the same ID.

    A unique identifier for the entity. For a relying party entity,
    sets the RP ID. For a user account entity, this will be an
    arbitrary string specified by the relying party.
    """
    return generate_challenge(20)


def get_origin(request):
    return "{scheme}://{host}".format(scheme=request.scheme, host=request.get_host())


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
