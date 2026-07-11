# core/tests/ui.py

# to avoid install playwright in the container when running test without ui
try:
  from playwright.sync_api import BrowserContext, Page, sync_playwright

  PLAYWRIGHT_AVAILABLE = True
except ImportError:
  PLAYWRIGHT_AVAILABLE = False

import os
import unittest

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.urls import reverse

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "True")


@tag("ui")
@unittest.skipUnless(PLAYWRIGHT_AVAILABLE, "playwright not installed")
class PlaywrightTestCase(StaticLiveServerTestCase):
  """
  Base class for UI tests with Playwright.

  Usage :
      class MyUITest(PlaywrightTestCase):
          def test_something(self):
              self.page.goto(self.url("/my-path/"))
              ...
  """

  # needed to avoid unauthenticated flatpage errors
  fixtures = ["predefined_flatpages.json"]

  # -- Overridable by subclasses --
  headless: bool = True
  browser_type: str = "chromium"  # "chromium" | "firefox" | "webkit"
  slow_mo: int = 0  # ms between each action (useful for debugging)
  default_timeout: int = 5_000  # ms, Playwright default timeout
  # Login involves a PBKDF2 password check + 302 redirect + target page render.
  # On slow CI containers (GitHub Actions, shared CPU) this can take several
  # seconds, so we use a generous timeout here rather than default_timeout.
  login_timeout: int = 30_000  # ms

  # ------------------------------------------------------------------ #
  #  Browser lifecycle (one instance per test class)                   #
  # ------------------------------------------------------------------ #

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls._playwright = sync_playwright().start()
    launcher = getattr(cls._playwright, cls.browser_type)
    cls._browser = launcher.launch(
      headless=cls.headless,
      slow_mo=cls.slow_mo,
    )

  @classmethod
  def tearDownClass(cls):
    cls._browser.close()
    cls._playwright.stop()
    super().tearDownClass()

  # ------------------------------------------------------------------ #
  #  Context / page lifecycle (one instance per test)                 #
  # ------------------------------------------------------------------ #

  def setUp(self) -> None:
    super().setUp()
    self.context: BrowserContext = self._browser.new_context()
    self.page: Page = self.context.new_page()
    self.page.set_default_timeout(self.default_timeout)
    self.user = get_user_model().objects.create_superuser(
      "admin",
      "admin@example.com",
      "password",
      first_name="Admin",
      last_name="User",
      birthdate="2000-01-01",
    )
    # errors tracking
    self.errors: list[str] = []
    self.page.on("pageerror", lambda err: self.errors.append(str(err)))
    # self.page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))

  def tearDown(self):
    self.page.close()
    self.context.close()
    self.assertFalse(self.errors, f"Page errors: {self.errors}")
    super().tearDown()

  # ------------------------------------------------------------------ #
  #  Helpers                                                            #
  # ------------------------------------------------------------------ #

  def url(self, path: str) -> str:
    """Builds an absolute URL from a relative path."""
    return f"{self.live_server_url}{path}"

  def login(self, username: str, password: str, *, next: str = "/") -> None:
    """
    Authenticates the user via the allauth login form.
    Override if your form uses different selectors.
    """
    self.page.goto(self.url(f"/accounts/login/?next={next}"))
    # Ensure the login form is fully loaded before filling
    self.page.wait_for_selector("input[name='login']", state="visible", timeout=self.login_timeout)
    self.page.fill("input[name='login']", username)
    self.page.fill("input[name='password']", password)
    # Click the login form's own submit button (the allauth template may render
    # additional submit buttons for passkey/code login; scope to the main form).
    self.page.click("form[action*='/accounts/login/'] button[type='submit']")
    # Wait for the URL to navigate away from the login page.
    # Use "domcontentloaded" instead of the default "load" to avoid timeouts
    # from slow CDN sub-resources (images, fonts) that delay the "load" event.
    # Use login_timeout (not default_timeout): the POST triggers a PBKDF2
    # check_password + 302 redirect + target page render, which can take several
    # seconds on slow CI containers (GitHub Actions) — well beyond 5s.
    try:
      self.page.wait_for_url(
        lambda url: "/login/" not in url,
        timeout=self.login_timeout,
        wait_until="domcontentloaded",
      )
    except Exception:
      # Diagnostic : capture the error message if login failed
      error_el = self.page.locator(".message.is-danger, .alert-danger, .errorlist.nonfield")
      if error_el.count() > 0:
        self.take_screenshot("login_failure")
        raise AssertionError(f"Login failed: {error_el.first.inner_text()}") from None
      self.take_screenshot("login_timeout")
      raise AssertionError(f"Login form submission did not navigate away from {self.page.url}") from None
    self.assert_url_not_contains("/login/")

  def assert_visible(self, selector: str, message: str | None = None) -> None:
    """Asserts that an element is visible (fails cleanly)."""
    locator = self.page.locator(selector)
    self.assertTrue(
      locator.is_visible(),
      message or f"Element '{selector}' is not visible.",
    )

  def assert_hidden(self, selector: str, message: str | None = None) -> None:
    locator = self.page.locator(selector)
    self.assertFalse(
      locator.is_visible(),
      message or f"Element '{selector}' should be hidden.",
    )

  def assert_url_contains(self, fragment: str, message: str | None = None) -> None:
    self.assertIn(fragment, self.page.url, message or f"URL should contain '{fragment}'")

  def assert_url_not_contains(self, fragment: str, message: str | None = None) -> None:
    self.assertNotIn(fragment, self.page.url, message or f"URL should not contain '{fragment}'")

  def take_screenshot(self, name: str = "screenshot") -> None:
    """Capture useful in case of debug or failure."""
    self.page.screenshot(path=f"/tmp/screenshots/{name}.png", full_page=True)

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

  def capture_screenshot_if_errors(self, test_name: str) -> None:
    """Capture screenshot on failure if errors were collected."""
    if self.errors:
      self.take_screenshot(f"failure_{test_name}")

  def goto_page(self, name: str, args={}, kwargs={}) -> None:
    self.page.goto(self.url(reverse(name, args=args, kwargs=kwargs)))

  def login_and_goto_page(self, name: str, args={}, kwargs={}) -> None:
    self.login("admin", "password")
    self.goto_page(name, args, kwargs)

  # Helper assertion to compare element counts – Playwright's locator.count() returns an int
  def assertEqual(self, first, second, msg=None):
    self.assertTrue(first == second, msg or f"{first!r} != {second!r}")
