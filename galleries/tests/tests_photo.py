from datetime import date
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from accounts.tests import CreatedAccountTestCase
from ..models import Photo, Gallery
from ..views.views_photo import PhotoAddView
from .utils import create_image, GalleryBaseTestCase
from .tests_gallery import get_gallery_name

COUNTER = 0


def get_photo_name():
  global COUNTER
  COUNTER += 1
  return "photo #" + str(COUNTER)


class CheckLoginRequired(CreatedAccountTestCase):
  def test_login_required(self):
    rurl = reverse('galleries:photo', args=[1])
    response = self.client.get(rurl)
    self.assertRedirects(response, self.next(self.login_url, rurl), 302, 200)


class PhotoTestsBase(GalleryBaseTestCase):

  def setUp(self):
    super().setUp()
    self.root_gallery = Gallery(name=get_gallery_name(), description="a test root gallery")
    self.root_gallery.save()
    self.sub_gallery = Gallery(name=get_gallery_name(), description="a test sub gallery", parent=self.root_gallery)
    self.sub_gallery.save()
    self.image = create_image("test-image-1.jpg")


class CreatePhotoTests(PhotoTestsBase):
  def test_create_photo_no_gallery(self):
    with self.assertRaises(ValidationError):
      p = Photo(name=get_photo_name(), date=date.today(), image=self.image, gallery=None)
      p.save()

  def test_create_photo_no_date(self):
    with self.assertRaises(ValidationError):
      p = Photo(name=get_photo_name(), image=self.image, gallery=self.root_gallery)
      p.save()

  def test_create_photo_no_image(self):
    with self.assertRaises(ValidationError):
      p = Photo(name=get_photo_name(), gallery=self.root_gallery, date=date.today(), description="a test photo")
      p.save()

  def test_create_photo(self):
    name = get_photo_name()
    p = Photo(name=name, gallery=self.root_gallery, date=date.today(), image=self.image, description="a test photo")
    p.save()
    self.assertTrue(Photo.objects.filter(name=name).exists())


class CreatePhotoViewTests(PhotoTestsBase):
  def test_create_photo_view(self):
    ap_url = reverse('galleries:add_photo', kwargs={'gallery': self.root_gallery.id})
    response = self.client.get(ap_url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/add_photo.html')
    self.assertIs(response.resolver_match.func.view_class, PhotoAddView)

    # print("response:", response)
    formdata = {'name': 'a photo', 'description': 'a description', 'gallery': self.root_gallery.id,
                'date': date.today()}
    formclass = PhotoAddView().get_form_class()
    form = formclass(data=formdata, files={'image': self.image})
    print(form.errors)  # doesn't print anything if there are no errors
    self.assertTrue(form.is_valid())

  def test_display_several_photos(self):
    # create some photos
    photos = []
    for i in range(4):
      image = create_image(f"test-image-{i+1}.jpg")
      p = Photo(name=get_photo_name(), gallery=self.root_gallery, date=date.today(), image=image)
      p.save()
      photos.append(p)

    url = reverse('galleries:detail', kwargs={'pk': self.root_gallery.id})
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/photos_gallery.html')
    for p in photos:
      self.assertContains(response, f'''
  <div class="cell">
    <a href="{reverse('galleries:photo', args=[p.id])}">
      <figure class="image is-128x128">
        <img src="{p.thumbnail.url}">
      </figure>
    </a>
  </div>
''', html=True)


class DeletePhotoViewTest(PhotoTestsBase):
  def test_delete_photo(self):
    # Create a photo
    name = get_photo_name()
    p = Photo(name=name, gallery=self.root_gallery, date=date.today(), image=self.image)
    p.save()

    # Delete the photo
    url = reverse('galleries:delete_photo', args=[p.id])
    response = self.client.post(url, follow=True)
    self.assertRedirects(response, reverse('galleries:detail', kwargs={'pk': self.root_gallery.id}), 302, 200)
    self.assertFalse(Photo.objects.filter(pk=p.id).exists())
    self.assertContainsMessage(response, "success", _('Photo deleted'))
