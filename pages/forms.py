from cm_main.widgets import RichTextarea
from django.contrib.flatpages.forms import FlatpageForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Value, F, Q
from django.db.models.functions import Substr, Length

from .models import FlatPage


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
      # check if the new url starts with some existing urls or reverse
      new_url_starts_w_existing_urls = FlatPage.objects.annotate(
              url_start=Substr(Value(new_url), 1, Length('url'))
          ).filter(
              Q(url_start=F('url')) | Q(url__startswith=new_url)
          )
      if self.instance.id:  # update, exclude the instance itself from the check
        new_url_starts_w_existing_urls = new_url_starts_w_existing_urls.exclude(pk=self.instance.id)

      if new_url_starts_w_existing_urls.exists():
        for page in new_url_starts_w_existing_urls:
          if page.url == new_url:
            raise ValidationError(
                 _("Flatpage with url %(url)s already exists") % {'url': new_url},
                 code="duplicate_url",
             )
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
