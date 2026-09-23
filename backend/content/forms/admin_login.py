"""Keep Django's staff/CSRF/session behavior behind the shared CAPTCHA check."""
from django import forms
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm

from projectapp.recaptcha import CaptchaError, captcha_enabled, verify_captcha


class CaptchaAdminAuthenticationForm(AdminAuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captcha_enabled = captcha_enabled()
        self.captcha_site_key = settings.RECAPTCHA_SITE_KEY
        self.fields['g-recaptcha-response'] = forms.CharField(
            required=False, widget=forms.HiddenInput, strip=True,
        )

    def clean(self):
        try:
            verify_captcha(self.cleaned_data.get('g-recaptcha-response', ''))
        except CaptchaError as exc:
            raise forms.ValidationError(exc.message, code=exc.code) from None
        return super().clean()
