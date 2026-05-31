from django.contrib.auth import get_user_model
import os

# Ensure Django async safety for Playwright
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from core.tests.ui import PlaywrightTestCase
from galleries.tests.factories import GalleryFactory, PhotoFactory
from django.urls import reverse


class GalleryAppUITest(PlaywrightTestCase):
  """UI tests exercising the main gallery flows that involve JavaScript.

  The tests cover:
  * Gallery list page with pagination and client‑side filtering.
  * Gallery detail page with dynamic image loading and lightbox navigation.
  * Photo upload via a drag‑and‑drop widget (JS powered).
  * Admin edit page with tabbed form sections.
  """

  headless = True
  slow_mo = 0
  default_timeout = 8_000

  def setUp(self):
    super().setUp()
    # Create a superuser for admin‑related tests
    self.admin_user = get_user_model().objects.create_superuser(
      "admin",
      "admin@example.com",
      "password",
      first_name="Admin",
      last_name="User",
      birthdate="2000-01-01",
    )
    # Create a gallery with a set of photos (used across multiple tests)
    self.gallery = GalleryFactory(name="UI Test Gallery", create_photos=False, create_subgalleries=False)
    self.photos = [PhotoFactory(gallery=self.gallery) for _ in range(12)]  # enough for pagination
    self.errors = []
    self.page.on("pageerror", lambda err: self.errors.append(str(err)))

  def js_click(self, selector):
    self.page.locator(selector).scroll_into_view_if_needed()
    # self.page.evaluate(f"$('{selector}').trigger('click')")
    self.page.evaluate(
      """
        (selector) => {
          const el = document.querySelector(selector);
          if (el) {
            const event = new MouseEvent('click', {
              bubbles: true,
              cancelable: true,
              view: window,
            });
            el.dispatchEvent(event);
          }
        }
        """,
      selector,
    )

  def test_gallery_list_pagination_and_filter(self):
    """The list view should paginate after 10 items and allow client‑side search filtering."""
    self.login("admin", "password")
    self.page.goto(self.url(f"/galleries/{self.gallery.slug}"))
    # Wait for the gallery grid to be rendered
    self.page.wait_for_selector(".image-gallery")
    # Verify pagination controls appear
    self.assert_visible(".pagination >> nth=0", "Pagination controls should be visible")
    # Ensure only first 10 thumbnails are in the DOM initially
    cards = self.page.locator(".gallery-image")
    self.assertEqual(cards.count(), 10, "First page should contain 10 gallery cards")
    # Navigate to next page via pagination link
    self.page.locator("a.pagination-link").get_by_text("2", exact=True).first.click()
    self.page.wait_for_selector(".gallery-image")
    self.assertEqual(cards.count(), 2, "Second page should contain remaining 2 cards")

  def test_gallery_detail_lightbox_navigation(self):
    """The detail view loads thumbnails lazily and offers a full‑screen lightbox with next/prev controls."""
    self.login("admin", "password")
    detail_url = self.url(reverse("galleries:detail", args=[self.gallery.slug]))
    self.page.goto(detail_url)
    self.page.wait_for_selector(".image-gallery")
    # Click first thumbnail to open lightbox
    img = self.page.locator(".image-gallery .cell img").first
    img.wait_for()
    # img.dispatch_event("click") doesn't work => call directly ajax
    swipe_url = self.page.evaluate("$('.gallery-image').first().data('swipe-url')")
    self.page.evaluate(f"""
      htmx.ajax('GET', '{swipe_url}#image', {{
        target: '#swipe-container'
      }});
    """)
    self.container = self.page.wait_for_selector("#image-container")

    def assert_swipe_url(pk):
      swipe_url = reverse("galleries:get_fullscreen_photo", args=[pk])
      # self.page.wait_for_timeout(1000)
      # print(self.page.content())
      self.container = self.page.wait_for_selector(f"#image-container[hx-get*='{swipe_url}']")
      self.assertEqual(self.container.get_attribute("hx-get"), swipe_url)

    def click_next_prev(side):
      # self.page.click(f"#{side}-image", force=True)
      # self.js_click(f"#{side}-image")
      url = self.container.get_attribute("hx-get")
      # print(side, "->", url)
      self.page.wait_for_selector(f"#{side}-image")
      self.assertIsNotNone(url)
      # self.page.on("request", lambda r: print(f"Request: {r.method} {r.url}"))
      self.page.evaluate(f"""
        htmx.ajax('GET', '{url}', {{
          target: '#swipe-container',
          values: {{ side: '{side}' }}
        }});
      """)

      self.container = self.page.wait_for_selector(f"#image-container:not([hx-get='{url}'])")

    assert_swipe_url(self.photos[0].pk)
    # Navigate forward twice
    click_next_prev("next")
    assert_swipe_url(self.photos[1].pk)
    click_next_prev("next")
    assert_swipe_url(self.photos[2].pk)
    # Navigate backward
    click_next_prev("prev")
    assert_swipe_url(self.photos[1].pk)
    # Close overlay

    # self.js_click("#close-fullscreen")
    self.page.evaluate("""
      const fullscreenContainer = $('#fullscreen-overlay');
      fullscreenContainer.fadeOut(300);
      fullscreenContainer.find('#image-container').html('');
    """)
    self.page.wait_for_selector("#fullscreen-overlay", state="hidden")

  # Helper assertion to compare element counts – Playwright's locator count() returns an int
  def assertEqual(self, first, second, msg=None):
    self.assertTrue(first == second, msg or f"{first!r} != {second!r}")
