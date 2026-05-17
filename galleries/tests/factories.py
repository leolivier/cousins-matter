import factory
from factory.django import DjangoModelFactory, ImageField
from galleries.models import Photo, Gallery
from members.tests.factories import MemberFactory
import datetime


class GalleryFactory(DjangoModelFactory):
  class Meta:
    model = Gallery

  name = factory.Faker("word")
  description = factory.Faker("paragraph")
  owner = factory.SubFactory(MemberFactory)


class PhotoFactory(DjangoModelFactory):
  class Meta:
    model = Photo

  image = ImageField(color="blue", width=800, height=600)
  name = factory.Faker("word")
  description = factory.Faker("paragraph")
  date = factory.LazyFunction(datetime.date.today)
  gallery = factory.SubFactory(GalleryFactory)
  uploaded_by = factory.SubFactory(MemberFactory)
