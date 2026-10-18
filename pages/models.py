from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage as _FlatPage
from django.db.models import BooleanField

from tenants.scoping import TenantModel


class FlatPage(TenantModel, _FlatPage):
  # predefined means imported from predefined pages
  predefined = BooleanField(default=False)
  # updated means that the page has been created in the UI or modified since last import
  updated = BooleanField(default=True)


def visible_pages():
  """FlatPages visible to the current request's tenant.

  With no active tenant (platform superuser, anonymous visitor,
  management commands), fall back to the default tenant — the same
  fallback TenantModel.ensure_tenant() uses on writes — otherwise the
  unfiltered manager returns every tenant's pages (the navbar menu
  renders the privacy policy once per tenant, and flatpage() raises
  MultipleObjectsReturned on URLs shared by two tenants).
  """
  # local imports: avoid circular imports with the tenants app
  from tenants.models import Tenant
  from tenants.scoping import get_current_tenant

  if get_current_tenant() is None:
    return FlatPage.objects.filter(tenant=Tenant.get_default())
  return FlatPage.objects.all()


def create_page(url, title, content):
  page = FlatPage.objects.create(url=url, title=title, content=content)
  page.sites.set([Site.objects.get(pk=settings.SITE_ID)])
  page.save()
  return page
