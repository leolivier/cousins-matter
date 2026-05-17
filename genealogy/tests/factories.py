import factory
from factory.django import DjangoModelFactory
from genealogy.models import Person, Family
from members.tests.factories import MemberFactory


class PersonFactory(DjangoModelFactory):
  class Meta:
    model = Person

  first_name = factory.Faker("first_name")
  last_name = factory.Faker("last_name")
  sex = factory.Iterator(["M", "F"])
  member = factory.SubFactory(MemberFactory)


class FamilyFactory(DjangoModelFactory):
  class Meta:
    model = Family

  partner1 = factory.SubFactory(PersonFactory, sex="M")
  partner2 = factory.SubFactory(PersonFactory, sex="F")
  union_type = "MARR"
