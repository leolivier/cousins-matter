from django import forms
from django.utils.translation import gettext_lazy as _


class SignupRequestForm(forms.Form):
  """Ask for a new family site: family name + email, protected by Turnstile."""

  tenant_name = forms.CharField(label=_("Family name"), max_length=200)
  email = forms.EmailField(label=_("Email"))

  def clean_tenant_name(self):
    return self.cleaned_data["tenant_name"].strip()
