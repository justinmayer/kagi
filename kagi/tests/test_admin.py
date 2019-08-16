from django.urls import reverse

import kagi.views


def test_get_admin_login_loads_the_form(client):
    response = client.get(reverse("admin:login"))
    assert isinstance(response.context_data["view"], kagi.views.KagiLoginView)


def test_get_admin_login_redirects_to_admin_index_if_already_logged_in(admin_client):
    response = admin_client.get(reverse("admin:login"))
    assert response.status_code == 302
    assert response.url == reverse("admin:index")
