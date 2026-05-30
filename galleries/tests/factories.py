import factory
import random
from factory.django import DjangoModelFactory, ImageField
from galleries.models import Photo, Gallery
from members.tests.factories import MemberFactory
import datetime


class GalleryFactory(DjangoModelFactory):
  class Meta:
    model = Gallery

  name = factory.Sequence(lambda n: f"Gallery {n}")
  description = factory.Faker("paragraph")
  owner = factory.SubFactory(MemberFactory)

  @factory.post_generation
  def create_photos(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    # Generate 3 to 10 photos
    for _ in range(random.randint(3, 10)):
      PhotoFactory(gallery=self, uploaded_by=self.owner)

  @factory.post_generation
  def create_subgalleries(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    # Only generate sub-galleries if this is a root gallery to keep a realistic 2-level hierarchy
    if self.parent is None:
      # Generate 1 to 3 sub-galleries
      for _ in range(random.randint(1, 3)):
        GalleryFactory(parent=self, owner=self.owner, create_subgalleries=False)


class PhotoFactory(DjangoModelFactory):
  class Meta:
    model = Photo

  image = ImageField(
    color=factory.LazyFunction(lambda: f"#{random.randint(0, 0xFFFFFF):06x}"),
    width=800,
    height=600,
  )
  name = factory.Sequence(lambda n: f"Photo {n}")
  description = factory.Faker("paragraph")
  date = factory.LazyFunction(datetime.date.today)
  gallery = factory.SubFactory(GalleryFactory)
  uploaded_by = factory.SubFactory(MemberFactory)
