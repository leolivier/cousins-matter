from datetime import date
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from cm_main.utils import create_test_image
from galleries.models import Photo, Gallery
from galleries.views.views_photo import PhotoAddView
from members.tests.tests_member import TestLoginRequiredMixin
from .tests_utils import GalleryBaseTestCase
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
    self.image = create_test_image(__file__, "test-image-1.jpg")


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

  def test_create_photo_too_big(self):
    image = create_test_image(__file__, "image-toobig.jpg")
    with self.assertRaises(ValidationError):
      p = Photo(name=get_photo_name(), gallery=self.root_gallery, date=date.today(),
                image=image, description="a too big photo")
      p.save()


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

  def get_several_photos(self, nb_photos, page_num, first, last, gallery):
    """
    Create nb_photos photos in this gallery if first page and return them in a list
    If not first page, the photos were created in first page, return a list containing only the page photos
    + the one just before and just after.
    """
    if page_num == 1:
      for i in range(nb_photos):
        image = create_test_image(__file__, f"test-image-{i+1}.jpg")
        p = Photo(name=get_photo_name(), gallery=gallery, date=date.today(), image=image)
        p.save()
    photos = Photo.objects.filter(gallery=gallery)[first:last]
    return photos

  def get_photo_dicts(self, photos, nb_photos, page_num, first, last):
    photo_dicts = [p.__dict__ for p in photos]
    nb_dicts = len(photo_dicts)
    for idx, p in enumerate(photo_dicts):
      if idx > 0:
        photo_dicts[idx-1]['next_url'] = p['image'].url
      if idx < nb_dicts - 1:
        photo_dicts[idx+1]['previous_url'] = p['image'].url

    # print('first, last, nb_photos:', first, last, nb_photos)

    if page_num > 1:
      del photo_dicts[0]  # remove the first photo of the page which is indeed the last of the previous page
    if last < nb_photos:  # not last page
      del photo_dicts[-1]  # remove the last photo of the page which is indeed the first of the next page
    return photo_dicts

  def check_display_several_photos(self, page_size, nb_photos, page_num=1, gallery=None):
    # create a sub gallery if not provided
    if gallery is None:
      gallery = Gallery(name=get_gallery_name(), description="a multi photo test sub gallery", parent=self.root_gallery)
      gallery.save()
    first = max(0, (page_size * (page_num - 1)) - 1)
    last = min((page_size * page_num) + 1, nb_photos)
    photos = self.get_several_photos(nb_photos, page_num, first, last, gallery)
    if page_num > 1:
      url = reverse('galleries:detail_page', kwargs={'pk': gallery.id, 'page': page_num}) + f"?page_size={page_size}"
    else:
      url = reverse('galleries:detail', kwargs={'pk': gallery.id}) + f"?page_size={page_size}"
    response = self.client.get(url)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/photos_gallery.html')
    photo_dicts = self.get_photo_dicts(photos, nb_photos, page_num, first, last)

    for idx, p in enumerate(photo_dicts):
      content = f'''
  <div class="cell has-text-centered">
    <figure class="image thumbnail mx-auto">
      <img src="{settings.MEDIA_URL}{p['thumbnail']}"
        class="gallery-image"
        {"data-next=" + p['next_url'] if 'next_url' in p else ""}
        data-fullscreen="{p['image'].url}"
        {"data-prev=" +  p['previous_url'] if 'previous_url' in p else ""}
        data-idx="{(page_num - 1) * page_size + idx + 1}"
        data-pk="{p['id']}"
      >
    </figure>
    <p>{p['name']}</p>
  </div>
    '''
      if idx < page_size:
        self.assertContains(response, content, html=True)
      else:
        self.assertNotContains(response, content, html=True)

    self.assertContains(response, f'''
<div id="fullscreen-overlay">
  <button id="close-fullscreen">{_("Close")}</button>
  <button id="prev-image" class="navigation-arrow">❮</button>
  <button id="next-image" class="navigation-arrow">❯</button>
  <div class="image-wrapper prev" style="transform: translateX(-100%);">
    <div class="image-container">
        <img src="">
    </div>
  </div>
  <div class="image-wrapper current">
    <div class="image-container">
        <img src="">
    </div>
  </div>
  <div class="image-wrapper next" style="transform: translateX(100%);">
    <div class="image-container">
        <img src="">
    </div>
  </div>
</div>
''', html=True)

    if nb_photos > (page_size * page_num):  # test next page
      self.check_display_several_photos(page_size, nb_photos, page_num + 1, gallery)

  def test_display_several_photos(self):
    self.check_display_several_photos(10, 9)
    self.check_display_several_photos(10, 12)

    self.check_display_several_photos(10, 11)


class DeletePhotoViewTest(PhotoTestsBase):
    def setUp(self):
        super().setUp()
        self.name = get_photo_name()
        self.photo = Photo(name=self.name, gallery=self.root_gallery, date=date.today(), image=self.image)
        self.photo.save()
        self.url = reverse('galleries:delete_photo', args=[self.photo.id])

    def test_delete_photo_no_owner(self):
        """Test deleting a photo with no owner (should succeed)"""
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse('galleries:detail', kwargs={'pk': self.photo.gallery.id}), 302, 200)
        self.assertFalse(Photo.objects.filter(pk=self.photo.id).exists())
        self.assertContainsMessage(response, "success", _('Photo deleted'))

    def test_delete_photo_as_owner(self):
        """Test deleting a photo as the photo owner"""
        self.photo.uploaded_by = self.member
        self.photo.save()
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse('galleries:detail', kwargs={'pk': self.photo.gallery.id}), 302, 200)
        self.assertFalse(Photo.objects.filter(pk=self.photo.id).exists())
        self.assertContainsMessage(response, "success", _('Photo deleted'))

    def test_delete_photo_as_gallery_owner(self):
        """Test deleting a photo as the gallery owner"""
        other_member = self.create_member()
        self.photo.uploaded_by = other_member
        self.photo.save()
        self.root_gallery.owner = self.member
        self.root_gallery.save()
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse('galleries:detail', kwargs={'pk': self.root_gallery.id}), 302, 200)
        self.assertFalse(Photo.objects.filter(pk=self.photo.id).exists())
        self.assertContainsMessage(response, "success", _('Photo deleted'))

    def test_delete_photo_unauthorized(self):
        """Test deleting a photo without proper permissions"""
        other_member = self.create_member()
        self.photo.uploaded_by = other_member
        self.photo.save()
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 403)  # Forbidden
        self.assertTrue(Photo.objects.filter(pk=self.photo.id).exists())

    def test_delete_nonexistent_photo(self):
        """Test deleting a photo that doesn't exist"""
        url = reverse('galleries:delete_photo', args=[99999])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 404)


class PhotoEditViewTest(PhotoTestsBase):
    def setUp(self):
        super().setUp()
        self.name = get_photo_name()
        self.photo = Photo(name=self.name, gallery=self.root_gallery, date=date.today(), image=self.image)
        self.photo.save()
        self.url = reverse('galleries:edit_photo', args=[self.photo.id])
        self.update_data = {
            'name': 'Updated photo name',
            'description': 'Updated description',
            'gallery': self.root_gallery.id,
            'date': date.today()
        }

    def test_edit_photo_no_owner(self):
        """Test editing a photo with no owner (should succeed)"""
        response = self.client.post(self.url, self.update_data, follow=True)
        self.assertRedirects(response, reverse('galleries:photo', kwargs={'pk': self.photo.id}), 302, 200)
        updated_photo = Photo.objects.get(pk=self.photo.id)
        self.assertEqual(updated_photo.name, 'Updated photo name')
        self.assertContainsMessage(response, "success", _("Photo updated successfully"))

    def test_edit_photo_as_owner(self):
        """Test editing a photo as the photo owner"""
        self.photo.uploaded_by = self.member
        self.photo.save()
        response = self.client.post(self.url, self.update_data, follow=True)
        self.assertRedirects(response, reverse('galleries:photo', kwargs={'pk': self.photo.id}), 302, 200)
        updated_photo = Photo.objects.get(pk=self.photo.id)
        self.assertEqual(updated_photo.name, 'Updated photo name')
        self.assertContainsMessage(response, "success", _("Photo updated successfully"))

    def test_edit_photo_unauthorized(self):
        """Test editing a photo without proper permissions"""
        other_member = self.create_member()
        self.photo.uploaded_by = other_member
        self.photo.save()
        response = self.client.post(self.url, self.update_data, follow=True)
        self.assertEqual(response.status_code, 403)  # Forbidden
        unchanged_photo = Photo.objects.get(pk=self.photo.id)
        self.assertEqual(unchanged_photo.name, self.name)

    def test_edit_nonexistent_photo(self):
        """Test editing a photo that doesn't exist"""
        url = reverse('galleries:edit_photo', args=[99999])
        response = self.client.post(url, self.update_data, follow=True)
        self.assertEqual(response.status_code, 404)
