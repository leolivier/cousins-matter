from django import forms
from django.conf import settings
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext_lazy as _

from cm_main.widgets import RichTextarea


class ContactForm(forms.Form):
    message = forms.CharField(label=_("Your message"), widget=RichTextarea, max_length=20000,
                              help_text=_("Please keep it short and avoid images."))
    attachment = forms.FileField(label=_('Attach file'), required=False,
                                 help_text=_("You can attach a file here if needed"),
                                 )


class PasswordResetForm(auth_forms.PasswordResetForm):
  def save(self,
           domain_override=None,
           subject_template_name="registration/password_reset_subject.txt",
           email_template_name="registration/password_reset_email.html",
           use_https=False,
           token_generator=default_token_generator,
           from_email=None,
           request=None,
           html_email_template_name=None,
           extra_email_context=None):
    extra_email_context = extra_email_context or {}
    extra_email_context['absolute_url'] = request.build_absolute_uri('/').rstrip('/') if request is not None else None

    extra_email_context['real_site_name'] = settings.SITE_NAME or domain_override or extra_email_context['absolute_url']
    domain_override = domain_override or settings.SITE_DOMAIN or extra_email_context['absolute_url']
    super().save(domain_override,
                 subject_template_name,
                 email_template_name,
                 use_https,
                 token_generator,
                 from_email,
                 request,
                 html_email_template_name,
                 extra_email_context)
