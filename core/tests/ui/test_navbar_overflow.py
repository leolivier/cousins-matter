# Throwaway UI test: navbar collapse behavior between Bulma's 1024px
# breakpoint and the ~1500px the menu actually needs.

from django.test import tag

from core.tests.ui.test_ui_base import PlaywrightTestCase


@tag("ui")
class NavbarOverflowTest(PlaywrightTestCase):
  def test_burger_shows_and_menu_is_reachable_at_narrow_widths(self):
    self.login_as_admin(next="/")
    for width in (1150, 1280):
      self.page.set_viewport_size({"width": width, "height": 900})
      self.page.goto(self.url("/"))
      burger = self.page.locator(".navbar-burger")
      self.assertTrue(burger.is_visible(), f"burger missing at {width}")
      burger.click()
      self.assertTrue(
        self.page.locator("#navMenu").is_visible(),
        f"menu should open on burger click at {width}",
      )
      for label in ("Members", "Genealogy"):
        self.assertTrue(
          self.page.locator(".navbar-start a.navbar-item", has_text=label).first.is_visible(),
          f"'{label}' not visible in burger menu at {width}",
        )
      self.page.screenshot(path=f"/tmp/screenshots/fix_burger_{width}.png")
      # dropdown opens on click inside the burger panel
      self.page.locator(".navbar-end .has-dropdown .navbar-link").first.click()
      self.assertTrue(
        self.page.locator(".navbar-end .navbar-dropdown").first.is_visible(),
        f"settings dropdown should open on click at {width}",
      )
    # wide screen: no burger, full menu
    self.page.set_viewport_size({"width": 1700, "height": 900})
    self.page.goto(self.url("/"))
    self.assertFalse(self.page.locator(".navbar-burger").is_visible())
    self.assertTrue(self.page.locator("#navMenu .navbar-end").is_visible())
