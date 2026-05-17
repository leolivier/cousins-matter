import factory
from factory.django import DjangoModelFactory
from members.models import Member, Family, Address
import datetime
import random


class FamilyFactory(DjangoModelFactory):
  class Meta:
    model = Family

  name = factory.Faker("last_name")


class AddressFactory(DjangoModelFactory):
  class Meta:
    model = Address

  number_and_street = factory.Faker("street_address")
  zip_code = factory.Faker("postcode")
  city = factory.Faker("city")
  country = factory.Faker("country_code")


class MemberFactory(DjangoModelFactory):
  class Meta:
    model = Member

  username = factory.Sequence(lambda n: f"user{n}_{random.randint(1000, 9999)}")
  first_name = factory.Faker("first_name")
  last_name = factory.Faker("last_name")
  email = factory.Sequence(lambda n: f"user{n}_{random.randint(1000, 9999)}@example.com")
  birthdate = factory.LazyFunction(lambda: datetime.date(1980, 1, 1) + datetime.timedelta(days=random.randint(0, 15000)))
  is_active = True
  family = factory.SubFactory(FamilyFactory)
  address = factory.SubFactory(AddressFactory)
  privacy_consent = True
