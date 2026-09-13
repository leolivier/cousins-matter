import factory
from factory.django import DjangoModelFactory, ImageField
from troves.models import Trove
from members.tests.factories import MemberFactory, DEFAULT_TENANT


class TroveFactory(DjangoModelFactory):
  class Meta:
    model = Trove

  # Troves belong to a tenant: default to the seeded default tenant so the
  # factory works with no ambient tenant_context (e.g. UI tests).
  tenant = DEFAULT_TENANT

  title = factory.Faker("sentence", nb_words=3)
  description = factory.Faker("paragraph")
  category = "history"
  owner = factory.SubFactory(MemberFactory)
  picture = ImageField(color="red", width=800, height=600)
