from django.conf import settings
from django.contrib import auth
from django.contrib.auth import load_backend
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.http import is_safe_url, urlencode
from django.views.generic import TemplateView

from ..forms import BackupCodeForm, SecondFactorForm, TOTPForm
from .mixin import OriginMixin


class KagiLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = "kagi/login.html"

    @property
    def is_admin(self):
        return self.template_name == "admin/login.html"

    def requires_two_factor(self, user):
        return (
            user.webauthn_keys.exists()
            or user.webauthn_keys.exists()
            or user.totp_devices.exists()
        )

    def form_valid(self, form):
        user = form.get_user()
        if not self.requires_two_factor(user):
            # no keys registered, use single-factor auth
            return super(KagiLoginView, self).form_valid(form)
        else:
            self.request.session["kagi_pre_verify_user_pk"] = user.pk
            self.request.session["kagi_pre_verify_user_backend"] = user.backend

            verify_url = reverse("kagi:verify-second-factor")
            redirect_to = self.request.POST.get(
                auth.REDIRECT_FIELD_NAME,
                self.request.GET.get(auth.REDIRECT_FIELD_NAME, ""),
            )
            params = {}
            if is_safe_url(
                url=redirect_to,
                allowed_hosts=[self.request.get_host()],
                require_https=True,
            ):
                params[auth.REDIRECT_FIELD_NAME] = redirect_to
            if self.is_admin:
                params["admin"] = 1
            if params:
                verify_url += "?" + urlencode(params)

            return HttpResponseRedirect(verify_url)

    def get_context_data(self, **kwargs):
        kwargs = super(KagiLoginView, self).get_context_data(**kwargs)
        kwargs[auth.REDIRECT_FIELD_NAME] = self.request.GET.get(
            auth.REDIRECT_FIELD_NAME, ""
        )
        kwargs.update(self.kwargs.get("extra_context", {}))
        return kwargs


class VerifySecondFactorView(OriginMixin, TemplateView):
    template_name = "kagi/verify_second_factor.html"

    @property
    def form_classes(self):
        ret = {}
        if self.user.webauthn_keys.exists():
            ret["webauthn"] = SecondFactorForm
        if self.user.backup_codes.exists():
            ret["backup"] = BackupCodeForm
        if self.user.totp_devices.exists():
            ret["totp"] = TOTPForm

        return ret

    def get_user(self):
        try:
            user_id = self.request.session["kagi_pre_verify_user_pk"]
            backend_path = self.request.session["kagi_pre_verify_user_backend"]
            assert backend_path in settings.AUTHENTICATION_BACKENDS
            backend = load_backend(backend_path)
            user = backend.get_user(user_id)
            if user is not None:
                user.backend = backend_path
            return user
        except (KeyError, AssertionError):
            return None

    def dispatch(self, request, *args, **kwargs):
        self.user = self.get_user()
        if self.user is None:
            return HttpResponseRedirect(reverse("kagi:login"))
        return super(VerifySecondFactorView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        forms = self.get_forms()
        form = forms[request.POST["type"]]
        if form.is_valid() and form.validate_second_factor():
            return self.form_valid(form, forms)
        else:
            return self.form_invalid(forms)

    def form_invalid(self, forms):
        return self.render_to_response(self.get_context_data(forms=forms))

    def get_form_kwargs(self):
        return {"user": self.user, "request": self.request, "appId": self.get_origin()}

    def get_forms(self):
        kwargs = self.get_form_kwargs()
        if self.request.method == "GET":
            forms = {key: form(**kwargs) for key, form in self.form_classes.items()}
        else:
            method = self.request.POST["type"]
            forms = {
                key: form(**kwargs)
                for key, form in self.form_classes.items()
                if key != method
            }
            forms[method] = self.form_classes[method](self.request.POST, **kwargs)
        return forms

    def get_context_data(self, **kwargs):
        if "forms" not in kwargs:
            kwargs["forms"] = self.get_forms()
        kwargs = super(VerifySecondFactorView, self).get_context_data(**kwargs)
        if self.request.GET.get("admin"):
            kwargs["base_template"] = "admin/base_site.html"
        else:
            kwargs["base_template"] = "base.html"
        kwargs["user"] = self.user
        return kwargs

    def form_valid(self, form, forms):
        del self.request.session["kagi_pre_verify_user_pk"]
        del self.request.session["kagi_pre_verify_user_backend"]

        auth.login(self.request, self.user)

        redirect_to = self.request.POST.get(
            auth.REDIRECT_FIELD_NAME, self.request.GET.get(auth.REDIRECT_FIELD_NAME, "")
        )
        if not is_safe_url(url=redirect_to, allowed_hosts=[self.request.get_host()]):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
        return HttpResponseRedirect(redirect_to)
