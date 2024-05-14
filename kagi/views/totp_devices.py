from base64 import b32decode, b32encode
from collections import OrderedDict
from io import BytesIO
import os
from urllib.parse import quote

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.utils.translation import gettext as _
from django.views.generic import FormView, ListView

import qrcode
from qrcode.image.svg import SvgPathFillImage

from ..constants import SESSION_TOTP_SECRET_KEY
from ..forms import TOTPForm
from ..models import TOTPDevice
from .mixin import OriginMixin


class AddTOTPDeviceView(OriginMixin, FormView):
    form_class = TOTPForm
    template_name = "kagi/totp_device.html"
    success_url = reverse_lazy("kagi:totp-devices")

    def get(self, request, *args: str, **kwargs):
        # When opening the view with a GET request, we treat it as a "add new
        # device" request. There, we create a new TOTP secret and put it into
        # the current user's session. Upon POST, the secret is read from the
        # session again.
        # Once a new TOTP device was successfully added, we'll drop the secret
        # from the session.
        # This approach allows to re-enter the token if mistyped, while keeping
        # the same TOTP device setup on the TOTP generator.
        self.secret = self.gen_secret()
        request.session[SESSION_TOTP_SECRET_KEY] = self.secret
        return super().get(request, *args, **kwargs)

    def post(self, request, *args: str, **kwargs):
        # Try to get the TOTP secret from the session. If the secret doesn't
        # exist, redirect to the view again, to configure a new TOTP secret.
        self.secret = request.session.get(SESSION_TOTP_SECRET_KEY, None)
        if not self.secret:
            messages.error(request, _("Missing TOTP secret. Please try again."))
            return redirect(request.path)

        return super().post(request, *args, **kwargs)

    def gen_secret(self):
        return b32encode(os.urandom(20)).decode()

    def get_otpauth_url(self, secret):
        issuer = get_current_site(self.request).name

        params = OrderedDict([("secret", secret), ("digits", 6), ("issuer", issuer)])

        return "otpauth://totp/{issuer}:{username}?{params}".format(
            issuer=quote(issuer),
            username=quote(self.request.user.get_username()),
            params=urlencode(params),
        )

    def get_qrcode(self, data):
        img = qrcode.make(data, image_factory=SvgPathFillImage)
        buf = BytesIO()
        img.save(buf)
        return buf.getvalue().decode("utf-8")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["base32_key"] = self.secret
        kwargs["otpauth"] = self.get_otpauth_url(self.secret)
        kwargs["qr_svg"] = self.get_qrcode(kwargs["otpauth"])
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            user=self.request.user, request=self.request, appId=self.get_origin()
        )
        return kwargs

    def form_valid(self, form):
        device = TOTPDevice(user=self.request.user, key=b32decode(self.secret))
        if device.validate_token(form.cleaned_data["token"]):
            del self.request.session[SESSION_TOTP_SECRET_KEY]
            device.save()
            messages.success(self.request, _("Device added."))
            return super().form_valid(form)
        else:
            assert not device.pk
            form.add_error("token", TOTPForm.INVALID_ERROR_MESSAGE)
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Should this go in Django's FormView?!
        # <https://code.djangoproject.com/ticket/25548>
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if "next" in self.request.GET and url_has_allowed_host_and_scheme(
            self.request.GET["next"], allowed_hosts=[self.request.get_host()]
        ):
            return self.request.GET["next"]
        else:
            return super().get_success_url()


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
