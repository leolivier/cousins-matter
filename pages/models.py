from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage as _FlatPage
from django.db.models import BooleanField


class FlatPage(_FlatPage):
  # predefined means imported from predefined pages
  predefined = BooleanField(default=False)
  # updated means that the page has been created in the UI or modified since last import
  updated = BooleanField(default=True)


def create_page(url, title, content):
  page = FlatPage.objects.create(url=url, title=title, content=content)
  page.sites.set([Site.objects.get(pk=settings.SITE_ID)])
  page.save()
  return page
