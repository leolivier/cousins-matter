from cm_main.widgets import RichTextarea
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.forms import FlatpageForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Value, F
from django.db.models.functions import Substr, Length


class PageForm(FlatpageForm):
    class Meta:
        model = FlatPage
        fields = ['url', 'title', 'content', 'registration_required']
        widgets = {
          "content": RichTextarea(),
        }

    def clean_url(self):
      new_url = super().clean_url()
      assert new_url is not None
      # check if the new url starts with some existing urls
      new_url_starts_with_existing_urls = FlatPage.objects.annotate(
              url_start=Substr(Value(new_url), 1, Length('url'))
          ).filter(
              url_start=F('url')
          )
      # check if some existing urls starts with the new url
      existing_urls_starting_with_new_url = FlatPage.objects.filter(url__startswith=new_url)
      if self.instance.id:  # update, exclude the instance itself from the check
        new_url_starts_with_existing_urls = new_url_starts_with_existing_urls.exclude(pk=self.instance.id)
        existing_urls_starting_with_new_url = existing_urls_starting_with_new_url.exclude(pk=self.instance.id)

      if new_url_starts_with_existing_urls.exists() or existing_urls_starting_with_new_url.exists():
        raise ValidationError(
                _("A flatpage cannot be a subpage of another flatpage, check your URLs"),
                code="same_start_url",
            )
      return new_url

    def clean(self):
      if not self.instance.id:  # creation
        self.instance.registration_required = False
        self.instance.template_name = ''

      return super().clean()
