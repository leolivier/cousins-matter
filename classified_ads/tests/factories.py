import factory
import random
from factory.django import DjangoModelFactory, ImageField
from classified_ads.models import ClassifiedAd, AdPhoto
from members.tests.factories import MemberFactory


class ClassifiedAdFactory(DjangoModelFactory):
  class Meta:
    model = ClassifiedAd

  title = factory.Faker("sentence", nb_words=4)
  category = "home"  # Assuming "home" is a valid category key
  subcategory = "furniture"
  description = factory.Faker("paragraph")
  price = factory.LazyAttribute(lambda o: f"{random.randint(10, 1000)} €")
  owner = factory.SubFactory(MemberFactory)

  @factory.post_generation
  def create_photos(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    # Generate 1 to 4 photos
    for _ in range(random.randint(1, 4)):
      AdPhotoFactory(ad=self)


class AdPhotoFactory(DjangoModelFactory):
  class Meta:
    model = AdPhoto

  ad = factory.SubFactory(ClassifiedAdFactory)
  image = ImageField(
    color=factory.LazyFunction(lambda: f"#{random.randint(0, 0xFFFFFF):06x}"),
    width=400,
    height=300,
  )
