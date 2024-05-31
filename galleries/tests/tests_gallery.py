import os
from django.conf import settings
from datetime import date
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext as _

from accounts.tests import CreatedAccountTestCase
from ..models import Gallery, Photo
from .utils import create_image, GalleryBaseTestCase
from ..views.views_gallery import GalleryCreateView, GalleryDetailView, GalleryUpdateView

COUNTER = 0


def get_gallery_name():
  global COUNTER
  COUNTER += 1
  return "root gallery" + str(COUNTER)


class CheckLoginRequired(CreatedAccountTestCase):
  def test_login_required(self):
    for url in ['galleries:galleries', 'galleries:create']:
      rurl = reverse(url)
      response = self.client.get(rurl)
      # checks that the response is a redirect (302) to the login page
      # with another redirect afterward to the original url
      self.assertRedirects(response, self.next(self.login_url, rurl), 302, 200)

    for url in ['galleries:edit', 'galleries:detail', 'galleries:add_photo']:
      rurl = reverse(url, args=[1])
      response = self.client.get(rurl)
      self.assertRedirects(response, self.next(self.login_url, rurl), 302, 200)


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
    self.assertTemplateUsed(response, 'galleries/create_gallery.html')
    self.assertIs(response.resolver_match.func.view_class, GalleryCreateView)
    # check rich editor by class richtextarea, the rest is dynamic in the browser, can't be tested
    self.assertContains(response, 
                        '''<div class="control"> <textarea name="description" cols="40" rows="10"
                           maxlength="3000" class="richtextarea" id="id_description"> </textarea> </div>''',
                        html=True)

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
    # print(response.content)
    # get the sub gallery by name and parent
    sg = Gallery.objects.filter(name=sgal_name, parent=rg).first()
    self.assertIsNotNone(sg)
    # check redirects to the newly created gallery detail
    self.assertRedirects(response, reverse("galleries:detail", args=[sg.id]), 302, 200)
    # check the response contains the sub gallery details (name, photo count)
    self.assertContains(response, f'''<div class="media-content">
  <h1 class="title">{sg.name}</h1>
    <p class="content">{sg.description}</p>
</div>''', html=True)
    # check root gallery has the sub gallery for child
    self.assertTrue(rg.children.first().name == sgal_name)
    # check the root gallery appears as the parent gallery in the details
    self.assertContains(response, f'''<a class="button" href="{reverse('galleries:detail', args=[rg.id])}" 
      title="{_("Back to %(gname)s") % {'gname': rg.name}}">
      <span class="icon is-large">
        <i class="mdi mdi-24px mdi-arrow-up-right"></i>
      </span>
    </a>''', html=True)

    # check the sub gallery appears in the root gallery children list
    response = self.client.get(reverse("galleries:detail", args=[rg.id]), follow=True)
    url = reverse("galleries:detail", args=[sg.id])
    self.assertContains(response, f'''<div class="container has-text-centered">
  <a class="mr-2" href="{url}">
    <figure class="image sub-gallery-cover" style="margin:auto">
      <img src="{sg.cover_url()}">
    </figure>
    <figcaption>{sg.name}</figcaption>
  </a>
</div>''', html=True)

  def test_modify_gallery(self):
    gal_name = get_gallery_name()
    rg = Gallery(name=gal_name)
    rg.save()
    url = reverse("galleries:edit", args=[rg.id])
    response = self.client.get(url, follow=True)
    self.assertTrue(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, GalleryUpdateView)
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
    gal = Gallery(name=name, parent=parent)
    gal.save()
    url = reverse("galleries:detail", args=[gal.id])
    html = f'''
<div class="box">
  <article class="media">
    <figure class="media-left">
      <a class="image gallery-cover" href="{url}">
        <img src="{settings.DEFAULT_GALLERY_COVER_URL}">
      </a>
    </figure>
    <div class="media-content">
      <a class="content has-text-primary-dark" href="{url}">
        <p>
          <strong>{gal.name}</strong>
          <br>{gal.description}<br>
          <small>{_("No photo")}</small>
        </p>
      </a>
      {self.rec_build_tree(n-1, gal)}
    </div>
  </article>
</div>
    '''
    return html

  def test_tree_view(self):
    htmls = self.rec_build_tree(4, None)
    url = reverse("galleries:galleries")
    response = self.client.get(url)
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
