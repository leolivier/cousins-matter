from datetime import date
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from members.tests.tests_member import TestLoginRequiredMixin
from ..models import Photo, Gallery
from ..views.views_photo import PhotoAddView
from .tests_utils import create_image, GalleryBaseTestCase
from .tests_gallery import get_gallery_name

COUNTER = 0


def get_photo_name():
  global COUNTER
  COUNTER += 1
  return "photo #" + str(COUNTER)


class CheckLoginRequired(TestLoginRequiredMixin, TestCase):
  def test_login_required(self):
    self.assertRedirectsToLogin('galleries:photo', args=[1])


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
    # print("response:", response)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/photo_form.html')
    self.assertIs(response.resolver_match.func.view_class, PhotoAddView)
    # check rich editor by class richtextarea, the rest is dynamic in the browser, can't be tested
    self.assertContains(response,
                        '''<div class="control"> <textarea name="description" cols="40" rows="10"
                           maxlength="3000" class="richtextarea" id="id_description"> </textarea> </div>''',
                        html=True)

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
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/photos_gallery.html')
    previous_photo = None
    photo_dicts = []
    for p in photos:
      photo_dict = p.__dict__
      photo_dicts.append(photo_dict)
      if previous_photo:
        previous_photo['next_url'] = p.image.url
        photo_dict['previous_url'] = previous_photo['image'].url
      previous_photo = photo_dict
    for p in photo_dicts:
      self.assertContains(response, f'''
  <div class="cell has-text-centered">
    <figure class="image thumbnail mx-auto">
      <img src="{settings.MEDIA_URL}{p['thumbnail']}"
        class="gallery-image"
        {"data-next=" + p['next_url'] if 'next_url' in p else ""}
        data-fullscreen="{p['image'].url}"
        {"data-prev=" +  p['previous_url'] if 'previous_url' in p else ""}
      >
    </figure>
    <p>{p['name']}</p>
  </div>
    ''', html=True)

    self.assertContains(response, f'''
<div id="fullscreen-overlay">
  <button id="close-fullscreen">{_("Close")}</button>
  <button id="prev-image" class="navigation-arrow">❮</button>
  <button id="next-image" class="navigation-arrow">❯</button>
  <img id="fullscreen-image" src="" alt="full screen image">
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
