import os
from django.conf import settings
from datetime import date
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext as _

from accounts.tests import CreatedAccountTestCase
from ..models import Gallery, Photo
from .utils import create_image, GalleryBaseTestCase
from ..views.views_gallery import GalleryCreateView, GalleryDisplayView, GalleryUpdateView

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

    for url in ['galleries:edit', 'galleries:display', 'galleries:add_photo']:
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
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'galleries/edit_gallery.html')
    self.assertIs(response.resolver_match.func.view_class, GalleryCreateView)

    gal_name = get_gallery_name()
    response = self.client.post(url, {'name': gal_name, 'description': "a test root gallery"}, follow=True)
    rg = Gallery.objects.filter(name=gal_name).first()
    self.assertIsNotNone(rg)
    self.assertTrue(rg.cover_url() == settings.DEFAULT_GALLERY_COVER_URL)

  def test_create_sub_gallery(self):
    rgal_name = get_gallery_name()
    rg = Gallery(name=rgal_name)
    rg.save()
    url = reverse("galleries:create")
    sgal_name = get_gallery_name()
    response = self.client.post(url, {'name': sgal_name, 'description': "a test sub gallery", 'parent': rg.id}, follow=True)
    self.assertTrue(response.status_code, 200)
    # print(response.content)
    sg = Gallery.objects.filter(name=sgal_name, parent=rg).first()
    self.assertIsNotNone(sg)
    self.assertRedirects(response, reverse("galleries:display", args=[sg.id]), 302, 200)
    self.assertContains(response, f'''<p>
  <strong class="title">{sg.name}</strong>
  <br>{sg.description}<br><small>{_("No photo")}</small>
</p>''', html=True)
    self.assertTrue(rg.children.first().name == sgal_name)
    self.assertContains(response, f'''<a href="{reverse("galleries:display", args=[rg.id])}">
  <figure class="image is-128x128">
    <img src="{settings.DEFAULT_GALLERY_COVER_URL}">
    <figcaption class="has-text-centered">{rg.name}</figcaption>
  </figure>
</a>''', html=True)

    response = self.client.get(reverse("galleries:display", args=[rg.id]), follow=True)
    url = reverse("galleries:display", args=[sg.id])
    self.assertContains(response, f'''<article class="media">
  <figure class="media-left">
    <a class="image is-128x128" href="{url}"><img src="{sg.cover_url()}"></a>
  </figure>
  <div class="media-content">
    <a class="content has-text-primary-dark" href="{url}">
      <p><strong>{sg.name}</strong>
        <br>{sg.description}<br>
        <small>{_("No photo")}</small>
      </p>
    </a>
  </div>
</article>''', html=True)

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
    self.assertIs(response.resolver_match.func.view_class, GalleryDisplayView)
    # print(response.content)
    rg.refresh_from_db()
    self.assertEqual(rg.name, gal_name)

  def rec_build_tree(self, n, parent):
    if n == 0:
      return ''
    name = get_gallery_name()
    gal = Gallery(name=name, parent=parent)
    gal.save()
    url = reverse("galleries:display", args=[gal.id])
    html = f'''
<div class="box">
  <article class="media">
    <figure class="media-left">
      <a class="image is-128x128" href="{url}">
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
