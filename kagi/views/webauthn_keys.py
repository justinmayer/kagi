from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import ListView, TemplateView

from ..forms import KeyRegistrationForm
from .mixin import OriginMixin


class AddWebAuthnKeyView(OriginMixin, TemplateView):
    template_name = "kagi/add_key.html"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["form"] = KeyRegistrationForm()
        return kwargs


class KeyManagementView(ListView):
    template_name = "kagi/key_list.html"

    def get_queryset(self):
        return self.request.user.webauthn_keys.all()

    def post(self, request):
        assert "delete" in self.request.POST
        key = get_object_or_404(self.get_queryset(), pk=self.request.POST["key_id"])
        key.delete()
        messages.success(request, _("Key removed."))
        return HttpResponseRedirect(reverse("kagi:webauthn-keys"))
