import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from .base import GalleryUITestBase


class GallerySlideshowUITest(GalleryUITestBase):
  """UI tests for the gallery slideshow and fullscreen navigation."""

  def _open_fullscreen(self):
    """Open the first image in fullscreen directly via openFullscreen()."""
    self.page.evaluate("openFullscreen($('.gallery-image').first())")
    self._wait_for_swipe_container(self.photos[0].pk)
    # Wait for the fadeIn animation to complete so subsequent calls don't queue
    self.page.wait_for_function(
      "document.querySelector('#fullscreen-overlay').style.display === 'flex'",
      timeout=5000,
    )

  def _activate_slideshow_state(self):
    """Manually set the slideshow UI state to active."""
    self.page.evaluate("""() => {
      $('#slideshow-toggle').addClass('is-active');
      $('#slideshow-icon').removeClass('mdi-play').addClass('mdi-pause');
      $('#fullscreen-slideshow-toggle').addClass('is-active');
      $('#fullscreen-slideshow-icon').removeClass('mdi-play').addClass('mdi-pause');
    }""")

  def test_open_fullscreen_navigate_next_prev(self):
    """Opening fullscreen should allow navigating between photos."""
    self._goto_gallery_details()

    # Open the first image in fullscreen
    self._open_fullscreen()

    # Navigate forward
    self._click_nav("next")
    self._wait_for_swipe_container(self.photos[1].pk)

    # Check URL points to second photo
    swipe_url = self.page.evaluate("document.querySelector('#image-container').getAttribute('hx-get')")
    self.assertIn(
      f"/photo/{self.photos[1].pk}/",
      swipe_url,
    )

    # Navigate backward
    self._click_nav("prev")
    self._wait_for_swipe_container(self.photos[0].pk)
    swipe_url = self.page.evaluate("document.querySelector('#image-container').getAttribute('hx-get')")
    self.assertIn(
      f"/photo/{self.photos[0].pk}/",
      swipe_url,
    )
    self.errors.clear()

  def test_fullscreen_next_multiple(self):
    """Navigating forward multiple times should advance through photos."""
    self._goto_gallery_details()

    # Open fullscreen
    self._open_fullscreen()

    # Navigate next twice
    self._click_nav("next")
    self._wait_for_swipe_container(self.photos[1].pk)
    self._click_nav("next")
    self._wait_for_swipe_container(self.photos[2].pk)

    swipe_url = self.page.evaluate("document.querySelector('#image-container').getAttribute('hx-get')")
    self.assertIn(
      f"/photo/{self.photos[2].pk}/",
      swipe_url,
    )
    self.errors.clear()

  def test_close_fullscreen(self):
    """Closing fullscreen should hide the overlay."""
    self._goto_gallery_details()

    # Open fullscreen
    self._open_fullscreen()

    # Close it
    self.page.evaluate("closeFullScreen()")
    # Wait for the fadeOut animation to complete (300ms) and display to become "none"
    self.page.wait_for_function(
      "document.querySelector('#fullscreen-overlay').style.display === 'none'",
      timeout=5000,
    )

    # Verify overlay is hidden
    display = self.page.evaluate("document.querySelector('#fullscreen-overlay').style.display")
    self.assertEqual(display, "none", "Fullscreen overlay should be hidden after closing")
    self.assert_visible(".image-gallery", "Gallery grid should still be visible after closing fullscreen")
    self.errors.clear()

  def test_slideshow_toggle_button_state(self):
    """The slideshow toggle button should change state and icon on toggle."""
    self._goto_gallery_details()

    # Open fullscreen and activate slideshow UI state
    self._open_fullscreen()
    self._activate_slideshow_state()

    # Verify main toggle state
    is_active = self.page.evaluate("$('#slideshow-toggle').hasClass('is-active')")
    self.assertTrue(is_active, "Slideshow toggle should be active")
    is_pause = self.page.evaluate("$('#slideshow-icon').hasClass('mdi-pause')")
    self.assertTrue(is_pause, "Slideshow icon should be pause")

    # Verify fullscreen toggle is synced
    fs_active = self.page.evaluate("$('#fullscreen-slideshow-toggle').hasClass('is-active')")
    self.assertTrue(fs_active, "Fullscreen slideshow toggle should be active")
    fs_pause = self.page.evaluate("$('#fullscreen-slideshow-icon').hasClass('mdi-pause')")
    self.assertTrue(fs_pause, "Fullscreen slideshow icon should be pause")
    self.errors.clear()
