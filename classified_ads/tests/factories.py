import factory
from factory.django import DjangoModelFactory, ImageField
from classified_ads.models import ClassifiedAd, AdPhoto
from members.tests.factories import MemberFactory

import random


class ClassifiedAdFactory(DjangoModelFactory):
  class Meta:
    model = ClassifiedAd

  title = factory.Faker("sentence", nb_words=4)
  category = "home"  # Assuming "home" is a valid category key
  subcategory = "furniture"
  description = factory.Faker("paragraph")
  price = factory.LazyAttribute(lambda o: f"{random.randint(10, 1000)} €")
  owner = factory.SubFactory(MemberFactory)


class AdPhotoFactory(DjangoModelFactory):
  class Meta:
    model = AdPhoto

  ad = factory.SubFactory(ClassifiedAdFactory)
  image = ImageField(color="green", width=400, height=300)
