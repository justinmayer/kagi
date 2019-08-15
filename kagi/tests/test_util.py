from django.conf import settings

from ..util import get_origin

settings.configure()


def test_get_origin(rf):
    request = rf.get("/")
    origin = get_origin(request)
    assert origin == "http://testserver", "Origin should be 'testserver' over HTTP"
