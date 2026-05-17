import factory
from factory.django import DjangoModelFactory
from pages.models import FlatPage
from django.contrib.sites.models import Site
from django.conf import settings


class FlatPageFactory(DjangoModelFactory):
  class Meta:
    model = FlatPage

  url = factory.Sequence(lambda n: f"/page-{n}/")
  title = factory.Faker("sentence")
  content = factory.Faker("paragraph")
  predefined = False
  updated = True

  @factory.post_generation
  def sites(self, create, extracted, **kwargs):
    if not create:
      return
    if extracted:
      for site in extracted:
        self.sites.add(site)
    else:
      self.sites.add(Site.objects.get(id=settings.SITE_ID))
