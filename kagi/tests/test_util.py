from ..util import get_origin


def test_get_origin(rf):
    request = rf.get("/")
    origin = get_origin(request)
    assert origin == "http://testserver", "Origin should be 'testserver' over HTTP"
