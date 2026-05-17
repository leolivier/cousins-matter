import factory
from factory.django import DjangoModelFactory, ImageField
from troves.models import Trove
from members.tests.factories import MemberFactory


class TroveFactory(DjangoModelFactory):
  class Meta:
    model = Trove

  title = factory.Faker("sentence", nb_words=3)
  description = factory.Faker("paragraph")
  category = "history"
  owner = factory.SubFactory(MemberFactory)
  picture = ImageField(color="red", width=800, height=600)
