from django.contrib.auth import get_user_model
import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from core.tests.ui import PlaywrightTestCase
from galleries.tests.factories import GalleryFactory, PhotoFactory


class GallerySlideshowUITest(PlaywrightTestCase):
  slow_mo = 0  # mettre ex. 200 pour débugger visuellement

  def setUp(self):
    super().setUp()
    self.user = get_user_model().objects.create_superuser(
      "admin",
      "admin@example.com",
      "password",
      first_name="Admin",
      last_name="User",
      birthdate="2000-01-01",
    )
    self.gallery = GalleryFactory(name="UI Test Gallery")
    self.photos = [PhotoFactory(gallery=self.gallery) for _ in range(5)]

  def test_slideshow_navigation(self):
    self.login("admin", "password")
    self.page.goto(self.url(f"/galleries/{self.gallery.slug}"))
    self.page.wait_for_selector(".gallery-image")

    self.page.click("#slideshow-toggle")
    self.page.wait_for_selector("#fullscreen-overlay")

    self.assert_visible("#next-image", "Le bouton suivant doit être visible")
    self.page.locator("#next-image").click(force=True)
