from base64 import b32decode, b32encode
from collections import OrderedDict
from io import BytesIO
import os
from urllib.parse import quote

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.http import is_safe_url, urlencode
from django.utils.translation import ugettext as _
from django.views.generic import FormView, ListView

import qrcode
from qrcode.image.svg import SvgPathImage

from ..forms import TOTPForm
from ..models import TOTPDevice
from .mixin import OriginMixin


class AddTOTPDeviceView(OriginMixin, FormView):
    form_class = TOTPForm
    template_name = "kagi/totp_device.html"
    success_url = reverse_lazy("kagi:totp-devices")

    def gen_key(self):
        return os.urandom(20)

    def get_otpauth_url(self, key):
        secret = b32encode(key)
        issuer = get_current_site(self.request).name

        params = OrderedDict([("secret", secret), ("digits", 6), ("issuer", issuer)])

        return "otpauth://totp/{issuer}:{username}?{params}".format(
            issuer=quote(issuer),
            username=quote(self.request.user.get_username()),
            params=urlencode(params),
        )

    def get_qrcode(self, data):
        img = qrcode.make(data, image_factory=SvgPathImage)
        buf = BytesIO()
        img.save(buf)
        return buf.getvalue().decode("utf-8")

    @cached_property
    def key(self):
        try:
            return b32decode(self.request.POST["base32_key"])
        except KeyError:
            return self.gen_key()

    def get_context_data(self, **kwargs):
        kwargs = super(AddTOTPDeviceView, self).get_context_data(**kwargs)
        kwargs["base32_key"] = b32encode(self.key).decode()
        kwargs["otpauth"] = self.get_otpauth_url(self.key)
        kwargs["qr_svg"] = self.get_qrcode(kwargs["otpauth"])
        return kwargs

    def get_form_kwargs(self):
        kwargs = super(AddTOTPDeviceView, self).get_form_kwargs()
        kwargs.update(
            user=self.request.user, request=self.request, appId=self.get_origin()
        )
        return kwargs

    def form_valid(self, form):
        device = TOTPDevice(user=self.request.user, key=self.key)
        if device.validate_token(form.cleaned_data["token"]):
            device.save()
            messages.success(self.request, _("Device added."))
            return super(AddTOTPDeviceView, self).form_valid(form)
        else:
            assert not device.pk
            form.add_error("token", TOTPForm.INVALID_ERROR_MESSAGE)
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Should this go in Django's FormView?!
        # <https://code.djangoproject.com/ticket/25548>
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if "next" in self.request.GET and is_safe_url(
            self.request.GET["next"], allowed_hosts=[self.request.get_host()]
        ):
            return self.request.GET["next"]
        else:
            return super(AddTOTPDeviceView, self).get_success_url()


class TOTPDeviceManagementView(ListView):
    template_name = "kagi/totpdevice_list.html"

    def get_queryset(self):
        return self.request.user.totp_devices.all()

    def post(self, request):
        assert "delete" in self.request.POST
        device = get_object_or_404(
            self.get_queryset(), pk=self.request.POST["device_id"]
        )
        device.delete()
        messages.success(request, _("Device removed."))
        return HttpResponseRedirect(reverse("kagi:totp-devices"))
