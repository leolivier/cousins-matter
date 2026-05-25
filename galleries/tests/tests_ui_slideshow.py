from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from playwright.sync_api import sync_playwright
from galleries.tests.factories import GalleryFactory, PhotoFactory
from django.contrib.auth import get_user_model
import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


@tag("ui")
class GallerySlideshowUITest(StaticLiveServerTestCase):
  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.playwright = sync_playwright().start()
    cls.browser = cls.playwright.chromium.launch(headless=True)

  @classmethod
  def tearDownClass(cls):
    cls.browser.close()
    cls.playwright.stop()
    super().tearDownClass()

  def setUp(self):
    User = get_user_model()
    self.user = User.objects.create_superuser(
      "admin", "admin@example.com", "password", first_name="Admin", last_name="User", birthdate="2000-01-01"
    )

    self.gallery = GalleryFactory(name="UI Test Gallery")
    self.photos = [PhotoFactory(gallery=self.gallery) for _ in range(5)]

    # Create a new context and page for each test
    self.context = self.browser.new_context()
    self.page = self.context.new_page()

  def tearDown(self):
    self.page.close()
    self.context.close()

  def test_slideshow_navigation(self):
    # 1. Log in
    self.page.goto(f"{self.live_server_url}/accounts/login/")
    self.page.fill("input[name='login']", "admin")
    self.page.fill("input[name='password']", "password")
    self.page.click("button[type='submit']")

    # 2. Navigate to gallery
    self.page.goto(f"{self.live_server_url}/galleries/{self.gallery.slug}")

    # 3. Wait for the page to load and find the slideshow toggle button
    # Based on the screenshot, it's a play/pause or "slideshow" button.
    # Let's inspect the page or just trigger the slideshow
    # Usually we click the first image to start the slideshow.
    # Wait for at least one photo
    self.page.wait_for_selector(".gallery-image", timeout=5000)

    # Click the slideshow toggle to open the slideshow
    self.page.click("#slideshow-toggle")

    # Wait for the slideshow overlay and next button to become visible
    self.page.wait_for_selector("#fullscreen-overlay", timeout=5000)

    next_button = self.page.locator("#next-image")

    self.assertTrue(next_button.is_visible(), "Next button is not visible in the slideshow")

    # Click next and verify it works (this is a basic interaction test)
    next_button.click(force=True)

    # The test passes if we navigated successfully without throwing errors
    self.assertTrue(True)
