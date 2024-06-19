from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.flatpages.models import FlatPage


def create_page(url, title, content):
  page = FlatPage.objects.create(url=url, title=title, content=content)
  page.sites.set([Site.objects.get(pk=settings.SITE_ID)])
  page.save()
  return page

