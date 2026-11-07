from core.widgets import RichTextarea
from django.contrib.flatpages.forms import FlatpageForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Value, F, Q
from django.db.models.functions import Substr, Length

from .models import FlatPage
from tenants.models import Tenant
from tenants.scoping import get_current_tenant


class PageForm(FlatpageForm):
  class Meta:
    model = FlatPage
    fields = ["url", "title", "content", "registration_required"]
    widgets = {
      "content": RichTextarea(),
    }

  def clean_url(self):
    new_url = super().clean_url()
    assert new_url is not None  # nosec B101
    # check if the new url starts with some existing urls or reverse
    new_url_starts_w_existing_urls = FlatPage.objects.annotate(url_start=Substr(Value(new_url), 1, Length("url"))).filter(
      Q(url_start=F("url")) | Q(url__startswith=new_url)
    )
    if self.instance.id:  # update, exclude the instance itself from the check
      new_url_starts_w_existing_urls = new_url_starts_w_existing_urls.exclude(pk=self.instance.id)

    if new_url_starts_w_existing_urls.exists():
      for page in new_url_starts_w_existing_urls:
        if page.url == new_url:
          raise ValidationError(
            _("Flatpage with url %(url)s already exists") % {"url": new_url},
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
      self.instance.template_name = ""

    return super().clean()


class AdminPageForm(FlatpageForm):
  """Admin form.

  Stock FlatpageForm checks (url, site) uniqueness on the unscoped
  django_flatpage table, but pages are per-tenant copies sharing one Site
  (cf. pages.0004_tenant): re-implement the check scoped to the edited
  page's tenant.
  """

  class Meta:
    model = FlatPage
    fields = "__all__"

  def clean(self):
    # skip stock FlatpageForm.clean(): its global (url, site) check trips on
    # other tenants' copies of the same URL
    cleaned_data = super(FlatpageForm, self).clean()
    url = cleaned_data.get("url")
    sites = cleaned_data.get("sites")
    tenant_id = self.instance.tenant_id or (get_current_tenant() or Tenant.get_default()).pk
    if url and sites:
      matching_urls = FlatPage.unscoped.filter(url=url, tenant_id=tenant_id)
      if self.instance.pk:
        matching_urls = matching_urls.exclude(pk=self.instance.pk)
      for site in sites:
        if matching_urls.filter(sites=site).exists():
          raise ValidationError(
            _("Flatpage with url %(url)s already exists for site %(site)s"),
            code="duplicate_url",
            params={"url": url, "site": site},
          )
    return cleaned_data
