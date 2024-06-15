from django import forms
from django.conf import settings
from cm_main.widgets import RichTextarea
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

pages_prefix = f'/{settings.PAGES_URL_PREFIX}/'


class PageForm(forms.ModelForm):
    url = forms.RegexField(
        label=_("URL"),
        max_length=100,
        regex=r"^[-\w/.~]+$",
        help_text=_(
            f"Example: “{pages_prefix}about/contact/”. Make sure to have leading {pages_prefix} and trailing "
            "slash."
        ),
        error_messages={
            "invalid": _(
                "This value must contain only letters, numbers, dots, "
                "underscores, dashes, slashes or tildes."
            ),
        },
    )

    class Meta:
        model = FlatPage
        fields = ['url', 'title', 'content', 'enable_comments']
        widgets = {
            "content": RichTextarea(),
        }

    def get_success_url(self):
        if self.object.url.startswith(pages_prefix):
            return self.object.url
        return super().get_success_url()

    def clean_url(self):
      url = self.cleaned_data["url"]
      if not url.startswith(pages_prefix):
        raise ValidationError(
           _(f"URLs MUST start with {pages_prefix}"),
           code="missing_leading_page_prefix")
      if not url.endswith("/"):
        raise ValidationError(
            _("URL is missing a trailing slash."),
            code="missing_trailing_slash")
      return url

    def clean(self):
        url = self.cleaned_data.get("url")
        same_url = FlatPage.objects.filter(url=url)
        if self.instance.pk:  # update
            same_url = same_url.exclude(pk=self.instance.pk)
            if same_url.exists():
              raise ValidationError(
                        _("Flatpage with url %(url)s already exists"),
                        code="duplicate_url",
                        params={"url": url},
                    )

        else:  # creation
          self.instance.registration_required = False
          self.instance.template_name = ''
        return super().clean()
