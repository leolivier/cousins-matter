import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.urls import reverse

from core.tests.ui import PlaywrightTestCase
from galleries.tests.factories import GalleryFactory, PhotoFactory


class GalleryUITestBase(PlaywrightTestCase):
  """UI tests base for the gallery."""

  def setUp(self):
    super().setUp()
    self.gallery = GalleryFactory(
      name="UI Test Gallery",
      create_photos=False,
      create_subgalleries=False,
    )
    self.photos = [PhotoFactory(gallery=self.gallery) for _ in range(12)]

  # ------------------------------------------------------------------
  # Helpers
  # ------------------------------------------------------------------

  def _wait_for_swipe_container(self, photo_pk=None, timeout=5000):
    """Wait for the swipe-container to have loaded a photo's content.
    If photo_pk is given, wait for that specific photo's hx-get attribute.
    """
    if photo_pk:
      swipe_url = reverse("galleries:get_fullscreen_photo", args=[photo_pk])
      return self.page.wait_for_selector(f"#image-container[hx-get='{swipe_url}']", timeout=timeout)
    return self.page.wait_for_selector("#image-container img, #image-container video", timeout=timeout)

  def _click_nav(self, side):
    """Navigate to next or prev using htmx.ajax, since Playwright's click doesn't work."""
    container = self.page.query_selector("#image-container")
    url = container.get_attribute("hx-get") if container else None
    if url:
      self.page.evaluate(
        f"""
        htmx.ajax('GET', '{url}', {{
          target: '#swipe-container',
          values: {{ side: '{side}' }}
        }});
      """
      )
      self.page.wait_for_selector(f"#image-container:not([hx-get='{url}'])")
      return True
    return False

  def _goto_gallery_details(self):
    self.login_and_goto_page("galleries:detail", args=[self.gallery.slug])
    # Wait for the gallery grid to be rendered
    self.assert_visible(".image-gallery", "Gallery grid should be visible")
    # Inject the galleries JS explicitly if not already loaded
    if not self.page.evaluate("typeof openFullscreen === 'function'"):
      self.page.add_script_tag(path="/home/olivier/devt/cousins-matter/galleries/static/galleries/js/galleries.min.js")
    # Wait for the JS function to be available
    self.page.wait_for_function("typeof openFullscreen === 'function'", timeout=3000)
    self.errors.clear()
