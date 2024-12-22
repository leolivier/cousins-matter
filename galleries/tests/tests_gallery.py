import os
from django.conf import settings
from datetime import date
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from cm_main.templatetags.cm_tags import icon
from members.tests.tests_member_base import TestLoginRequiredMixin
from ..models import Gallery, Photo
from .tests_utils import create_image, GalleryBaseTestCase
from ..views.views_gallery import GalleryCreateView, GalleryDetailView, GalleryUpdateView

COUNTER = 0


def get_gallery_name():
  global COUNTER
  COUNTER += 1
  return "root gallery" + str(COUNTER)


class CheckLoginRequired(TestLoginRequiredMixin, TestCase):
  def test_login_required(self):
    for url in ['galleries:galleries', 'galleries:create']:
      self.assertRedirectsToLogin(url)

    for url in ['galleries:edit', 'galleries:detail', 'galleries:add_photo']:
      self.assertRedirectsToLogin(url, args=[1])


class CreateGalleryTest(GalleryBaseTestCase):
  def test_create_root_gallery(self):
    gal_name = get_gallery_name()
    rg = Gallery(name=gal_name, description="a test root gallery")
    rg.save()
    self.assertTrue(Gallery.objects.filter(name=gal_name).exists())
    # re read from db
    rg.refresh_from_db()
    self.assertTrue(rg.cover_url() == settings.DEFAULT_GALLERY_COVER_URL)

  def test_create_sub_gallery(self):
    rgal_name = get_gallery_name()
    rg = Gallery(name=rgal_name)
    rg.save()
    sgal_name = get_gallery_name()
    sg = Gallery(name=sgal_name, description="a test sub gallery", parent=rg)
    sg.save()
    self.assertTrue(Gallery.objects.filter(name=sgal_name, parent=rg).exists())
    self.assertTrue(Gallery.objects.get(name=rgal_name, parent=None).children.first().name == sgal_name)

  def test_create_gallery_with_cover(self):
    gal = Gallery(name=get_gallery_name(), description="a gallery with a cover")
    gal.save()
    cover_file = "test-image-1.jpg"
    cover_image = create_image(cover_file)
    cover = Photo(name="a cover", image=cover_image, date=date.today(), gallery=gal)
    cover.save()
    gal.cover = cover
    gal.save()
    gal_dir = os.path.join(settings.MEDIA_ROOT, settings.GALLERIES_DIR, gal.full_path())
    self.assertTrue(os.path.isfile(os.path.join(gal_dir, cover_file)))

  def test_create_galleries_with_same_name(self):
    rgal_name = get_gallery_name()
    rg = Gallery(name=rgal_name)
    rg.save()
    with self.assertRaises(ValidationError):
      Gallery(name=rgal_name).save()

    sgal_name = get_gallery_name()
    Gallery(name=sgal_name, parent=rg).save()
    with self.assertRaises(ValidationError):
      Gallery(name=sgal_name, parent=rg).save()


class CreateGalleryViewTest(GalleryBaseTestCase):
  def test_create_root_gallery(self):
    url = reverse("galleries:create")
    response = self.client.get(url)
    # print(response.content)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/gallery_form.html')
    self.assertIs(response.resolver_match.func.view_class, GalleryCreateView)
    # check rich editor by class richtextarea, the rest is dynamic in the browser, can't be tested
    self.assertContains(response,
                        '''<div class="control"> <textarea name="description" cols="40" rows="10"
                           maxlength="3000" class="richtextarea" id="id_description"> </textarea> </div>''',
                        html=True)
    # check cover field is empty
    self.assertContains(response, f'''
<div id="div_id_cover" class="field">
  <label for="id_cover" class="label">{_("Cover Photo")}</label>
  <div class="control">
    <div class="select">
      <select name="cover" id="id_cover">
        <option value="" selected="">---------</option>
      </select>
    </div>
  </div>
</div>''', html=True)
    gal_name = get_gallery_name()
    response = self.client.post(url, {'name': gal_name, 'description': "a test root gallery"}, follow=True)
    rg = Gallery.objects.filter(name=gal_name).first()
    self.assertIsNotNone(rg)
    self.assertTrue(rg.cover_url() == settings.DEFAULT_GALLERY_COVER_URL)

  def test_create_sub_gallery(self):
    # create a root gallery directly
    rgal_name = get_gallery_name()
    rg = Gallery(name=rgal_name)
    rg.save()
    # create a sub gallery through view
    url = reverse("galleries:create")
    sgal_name = get_gallery_name()
    response = self.client.post(url, {'name': sgal_name, 'description': "a test sub gallery", 'parent': rg.id}, follow=True)
    self.assertTrue(response.status_code, 200)
    # self.print_response(response)
    # get the sub gallery by name and parent
    sg = Gallery.objects.filter(name=sgal_name, parent=rg).first()
    self.assertIsNotNone(sg)
    # check redirects to the newly created gallery detail
    self.assertRedirects(response, reverse("galleries:detail", args=[sg.id]), 302, 200)
    # check the response contains the sub gallery details (name, photo count)
    self.assertContains(response, f'''
<div class="container">
  <figure class="image gallery-cover is-pulled-left mr-3 mb-3 is-flex is-align-items-center is-justify-content-center">
    <img src="{sg.cover_url()}">
  </figure>
  <span class="title is-4">{sg.name}</span>
  <span class="tag">{_("No photo")}</span>
  <p>{sg.description}</p>
</div>''', html=True)
    # check root gallery has the sub gallery for child
    self.assertTrue(rg.children.first().name == sgal_name)
    # check the root gallery appears as the parent gallery in the details
    self.assertContains(response, f'''<a class="button" href="{reverse('galleries:detail', args=[rg.id])}"
      title="{_("Back to %(gname)s") % {'gname': rg.name}}">
      {icon('back')}
    </a>''', html=True)

    # check the sub gallery appears in the root gallery children list
    response = self.client.get(reverse("galleries:detail", args=[rg.id]), follow=True)
    # self.print_response(response)
    url = reverse("galleries:detail", args=[sg.id])
    self.assertContains(response, f'''
<p class="content has-text-centered mr-3">{_("Children galleries")}</p>
<div class="grid">
  <a class="cell mr-2" href="{url}">
    <figure class="image sub-gallery-cover mx-auto">
      <img src="{sg.cover_url()}">
    </figure>
    <p class="has-text-centered">{sg.name}</p>
  </a>
</div>''', html=True)

  def test_modify_gallery(self):
    # create a gallery
    gal_name = get_gallery_name()
    rg = Gallery(name=gal_name)
    rg.save()
    # add 3 photos in it
    photos = [Photo(name=f'Photo#{i+1}', image=create_image(f'test-image-{i+1}.jpg'), date=date.today(), gallery=rg)
              for i in range(3)]
    for p in photos:
      p.save()
    url = reverse("galleries:edit", args=[rg.id])
    response = self.client.get(url, follow=True)
    self.assertTrue(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, GalleryUpdateView)
    # check cover field contains the gallery photos
    self.assertContains(response, f'''
<div id="div_id_cover" class="field">
  <label for="id_cover" class="label">{_("Cover Photo")}</label>
  <div class="control">
    <div class="select">
      <select name="cover" id="id_cover">
        <option value="" selected="">---------</option>
        {"".join([f'<option value="{p.id}">{p}</option>' for p in photos])}
      </select>
    </div>
  </div>
</div>''', html=True)
    gal_name = get_gallery_name()
    response = self.client.post(url, {'name': gal_name, 'description': rg.description}, follow=True)
    self.assertTrue(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, GalleryDetailView)
    # print(response.content)
    rg.refresh_from_db()
    self.assertEqual(rg.name, gal_name)

  def rec_build_tree(self, n, parent):
    if n == 0:
      return ''
    name = get_gallery_name()
    gal = Gallery(name=name, parent=parent, description=f'a test gallery named {name}')
    gal.save()
    url = reverse("galleries:detail", args=[gal.id])
    html = f'''
<div class="container">
  <div class="section">
    <figure class="image gallery-cover is-pulled-left mr-3 mb-3">
      <a href="{url}">
        <img src="{gal.cover_url()}">
      </a>
    </figure>
    <a class="content has-text-primary-dark" href="{url}">
      <p>
        <strong>{gal.name}</strong>
        <span class="tag">{_("No photo")}</span>
        <br/>
        {gal.description}
      </p>
    </a>
    {self.rec_build_tree(n-1, gal)}
  </div>
</div>'''
    return html

  def test_tree_view(self):
    htmls = self.rec_build_tree(4, None)
    url = reverse("galleries:galleries")
    response = self.client.get(url)
    # self.print_response(response)
    self.assertContains(response, htmls, html=True)


class DeleteGalleryViewTest(GalleryBaseTestCase):
  def rec_build_tree(self, n, parent, image):
    # create n embedded galleries with one photo in each one
    if n == 0:
      return []
    gal = Gallery(name=get_gallery_name(), parent=parent)
    gal.save()
    p = Photo(name=get_gallery_name(), gallery=gal, date=date.today(), image=image)
    p.save()
    res = self.rec_build_tree(n-1, gal, image)
    return [(gal.id, p.id)] + res

  def test_delete_gallery(self):
    image = create_image("test-image-1.jpg")
    lst = self.rec_build_tree(3, None, image)
    # find the 1rst gallery below root
    gal = lst[1][0]
    self.assertIsNotNone(gal)
    # delete the gallery
    url = reverse("galleries:delete_gallery", kwargs={"pk": gal})
    response = self.client.get(url, follow=True)

    self.assertRedirects(response, reverse('galleries:galleries'), 302, 200)
    self.assertContainsMessage(response, "success", _('Gallery deleted'))
    # check root not removed
    gid, pid = lst[0]
    # print("gid/pid:", gid, pid)
    self.assertTrue(Gallery.objects.filter(pk=gid).exists())
    self.assertTrue(Photo.objects.filter(pk=pid).exists())
    # check others removed
    for gid, pid in lst[1:]:
      # print("gid/pid:", gid, pid)
      self.assertFalse(Gallery.objects.filter(pk=gid).exists())
      self.assertFalse(Photo.objects.filter(pk=pid).exists())
