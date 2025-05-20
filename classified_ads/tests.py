import random
import os
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.translation import gettext as _
from members.tests.tests_member import TestLoginRequiredMixin, MemberTestCase
from .forms import ClassifiedAdForm, AdPhotoForm
from .models import Categories, ClassifiedAd, AdPhoto
from .views import CreateAdView


def create_test_image():
  "Creates a dummy image file with minimal binary content and random ending"
  # 1 pixel gif with 1 bit per pixel
  image_content = b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"  # noqa
  # Adds between 1 and 16 random bytes at the end
  random_padding = os.urandom(random.randint(1, 16))
  return SimpleUploadedFile(
    name="test_image.gif",
    content=image_content + random_padding,
    content_type="image/gif"
  )


class ClassifiedAdBaseTestCase(TestLoginRequiredMixin, MemberTestCase):
  model = ClassifiedAd
  template_name = "classified_ads/form.html"
  form_class = ClassifiedAdForm

  def setUp(self):
    super().setUp()
    self.login()
    self.ad = {
      "title": "My car",
      "category": "vehicles",
      "subcategory": "cars",
      "description": "I sell my car",
      "item_status": "good",
      "ad_status": "for_sale",
      "price": "100$",
      "location": "my house",
      "shipping_method": "pickup",
    }

  def tearDown(self):
    super().tearDown()
    ClassifiedAd.objects.all().delete()
    AdPhoto.objects.all().delete()

  def check_ad(self):
    self.assertEqual(ClassifiedAd.objects.count(), 1)
    ad = ClassifiedAd.objects.first()
    self.assertEqual(ad.title, self.ad["title"])
    self.assertEqual(ad.owner, self.member)
    self.assertEqual(ad.category, self.ad["category"])
    self.assertEqual(ad.subcategory, self.ad["subcategory"])
    self.assertEqual(ad.description, self.ad["description"])
    self.assertEqual(ad.item_status, self.ad["item_status"])
    self.assertEqual(ad.ad_status, self.ad["ad_status"])
    self.assertEqual(ad.price, self.ad["price"])
    self.assertEqual(ad.location, self.ad["location"])
    self.assertEqual(ad.shipping_method, self.ad["shipping_method"])
    return ad

  def check_ad_response(self, response):
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, self.ad["title"])
    self.assertContains(response, self.member.full_name)
    self.assertContains(response, _(Categories.display_category(self.ad["category"])))
    self.assertContains(response, _(Categories.display_subcategory(self.ad["category"], self.ad["subcategory"])))
    self.assertContains(response, self.ad["price"])
    self.assertContains(response, _(dict(ClassifiedAd.ITEM_STATUS_TYPES).get(self.ad["item_status"])))


class ClassifiedAdCreateTestCase(ClassifiedAdBaseTestCase):

  def test_create_ad(self):
    url = reverse("classified_ads:create")
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'classified_ads/form.html')
    self.assertIs(response.resolver_match.func.view_class, CreateAdView)

    response = self.client.post(url, self.ad, follow=True)
    self.check_ad_response(response)
    self.check_ad()


class ClassifiedAdUpdateTestCase(ClassifiedAdBaseTestCase):

  def test_update_ad(self):
    self.ad["owner"] = self.member
    ad = ClassifiedAd.objects.create(**self.ad)
    url = reverse("classified_ads:update", kwargs={"pk": ad.id})

    # change price
    self.ad["price"] = "90$"

    response = self.client.post(url, self.ad, follow=True)
    self.check_ad_response(response)
    self.check_ad()

    # with self.assertRaises(ValidationError):
    #   self.client.post(url, self.ad)
    # self.assertEqual(ClassifiedAd.objects.count(), 1)

  def test_add_photos(self):
    self.ad["owner"] = self.member
    ad = ClassifiedAd.objects.create(**self.ad)
    url = reverse("classified_ads:add_photo", kwargs={"pk": ad.id})

    # add photos
    photos = []
    nphotos = 4
    for i in range(nphotos):
      photo = create_test_image()
      photos.append(photo)
      data = {'image': photo}
      form = AdPhotoForm(data=data, files={'image': photo})
      self.assertTrue(form.is_valid())

      response = self.client.post(url, data, format='multipart', follow=True)
      self.assertEqual(response.status_code, 200)

    ad = self.check_ad()
    self.assertEqual(AdPhoto.objects.count(), nphotos)
    for photo in AdPhoto.objects.all():
      self.assertEqual(photo.ad, ad)

    # delete photos
    for photo in AdPhoto.objects.all():
      url = reverse("classified_ads:delete_photo", kwargs={"pk": photo.id})
      response = self.client.post(url, follow=True, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
      self.assertEqual(response.status_code, 200)
      self.assertEqual(AdPhoto.objects.count(), nphotos - 1)
      nphotos = nphotos - 1

    self.assertEqual(AdPhoto.objects.count(), 0)


class DeleteAdTestCase(ClassifiedAdBaseTestCase):

  def test_delete_ad(self):
    self.ad["owner"] = self.member
    ad = ClassifiedAd.objects.create(**self.ad)
    for i in range(2):
      image = create_test_image()
      AdPhoto.objects.create(ad=ad, image=image)
    self.assertEqual(AdPhoto.objects.count(), 2)
    self.assertEqual(AdPhoto.objects.filter(ad=ad).count(), 2)

    url = reverse("classified_ads:delete", kwargs={"pk": ad.id})

    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(ClassifiedAd.objects.count(), 0)
    self.assertEqual(AdPhoto.objects.count(), 0)


class ListAdTestCase(ClassifiedAdBaseTestCase):

  def test_list_ad(self):
    self.ad["owner"] = self.member
    ad1 = ClassifiedAd.objects.create(**self.ad)
    self.ad2 = {
      "title": "My house",
      "category": "real_estate",
      "subcategory": "house",
      "description": "I sell my house",
      "item_status": "good",
      "ad_status": "for_sale",
      "price": "400.000$",
      "location": "my house",
      "shipping_method": "pickup",
      "owner": self.member,
    }
    ad2 = ClassifiedAd.objects.create(**self.ad2)

    url = reverse("classified_ads:list")
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'classified_ads/list.html')
    self.assertEqual(ClassifiedAd.objects.count(), 2)

    for ad in [ad1, ad2]:
      self.assertContains(response, f"""
<div class="panel-block is-flex">
  <span class="is-flex-grow-1">
    <span class="panel-icon is-large">
      <i class="mdi mdi-24px mdi-file-document" aria-hidden="true"></i>
    </span>
    <span class="mx-1">{ad.display_category()}</span>/
    <span class="mx-1">{ad.display_subcategory()}</span>/
    <span class="mx-1 has-background-primary has-text-white">{ad.display_item_status()}</span>
    <a href="{reverse("classified_ads:detail", kwargs={"pk": ad.id})}">{ad.title}</a> ({ad.price})
  </span>
  <span>
    {_(f"Added by %(owner)s on %(date_created)s") %
     {"owner": ad.owner.full_name,
     "date_created": formats.date_format(ad.date_created, "SHORT_DATE_FORMAT")}}
  </span>
</div>
""", html=True)


class DetailAdTestCase(ClassifiedAdBaseTestCase):

  def test_detail_ad(self):
    self.ad["owner"] = self.member
    ad = ClassifiedAd.objects.create(**self.ad)
    # add photos
    for i in range(4):
      image = create_test_image()
      AdPhoto.objects.create(ad=ad, image=image)

    url = reverse("classified_ads:detail", kwargs={"pk": ad.id})

    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'classified_ads/detail.html')
    localtime = timezone.localtime(ad.date_created)
    self.assertContains(response, f"""
<div class="panel-heading is-flex">
  <span class="icon is-medium mr-1">
    <i class="mdi mdi-24px mdi-file-document" aria-hidden="true"></i>
  </span>
  <span class="is-flex-grow-1">{ad.title}</span>
  <span>{_(f"Added by %(owner)s on %(date_created)s") %
  {"owner": ad.owner.full_name,
  "date_created": formats.date_format(localtime, "SHORT_DATETIME_FORMAT")}}</span>
</div>
<div class="panel-block is-flex">
  <div class="fixed-grid has-3-cols is-flex-grow-1">
    <div class="grid">
      <div class="cell"><strong>{_('Category')}:</strong>{ad.display_category()}</div>
      <div class="cell"><strong>{_('Subcategory')}:</strong>{ad.display_subcategory()}</div>
      <div class="cell"><strong>{_('State')}:</strong>{_(ad.display_item_status())}</div>
    </div>
  </div>
</div>
<div class="panel-block">{ad.description}</div>
<div class="panel-block is-flex">
  <div class="fixed-grid has-3-cols is-flex-grow-1">
    <div class="grid">
      <div class="cell"><strong>{_('Price')}:</strong>{ad.price}</div>
      <div class="cell"><strong>{_('Location')}:</strong>{ad.location}</div>
      <div class="cell"><strong>{_('Shipping')}:</strong>{_(ad.display_shipping_method())}</div>
    </div>
  </div>
</div>""", html=True)

    for photo in ad.photos.all():
      self.assertContains(response, f"""
        <div
          class="cell has-text-centered photo-item"
          id="photo-{photo.id}"
          data-pk="{photo.id}"
          data-fullscreen="{photo.image.url}"
        >
          <figure class="image thumbnail mx-auto">
            <img src="{photo.thumbnail.url}" alt="{_('Photo')}">
          </figure>
        </div>""", html=True)
