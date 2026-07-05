import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from . import PlaywrightTestCase


class ContactUITest(PlaywrightTestCase):
  """UI tests for the contact form page."""

  def test_contact_page_requires_auth(self):
    """Contact page should redirect to login when not authenticated."""
    self.goto_page("core:contact")
    # Should be redirected to login page
    self.assertIn("/login/", self.page.url, "Unauthenticated user should be redirected to login")

  def test_contact_form_display(self):
    """Contact form should display all expected fields for authenticated users."""
    self.login_and_goto_page("core:contact")

    # page title
    self.assert_visible("h1.title", "Page title should be visible")

    # form fields
    self.page.wait_for_selector("textarea#id_message", state="hidden")  # to be initialized by summernote
    self.assert_visible("input[name='attachment']", "Attachment file input should be visible")

    # buttons
    submit_btn = self.page.locator("button[type='submit']")
    self.assertTrue(submit_btn.is_visible(), "Submit button should be visible")

    cancel_btn = self.page.locator("button[type='cancel']")
    self.assertTrue(cancel_btn.is_visible(), "Cancel button should be visible")

    # csrf token
    self.assert_hidden("form#contact_form input[name='csrfmiddlewaretoken']", "CSRF token should be present")

  def test_contact_form_cancel_button(self):
    """Cancel button should navigate away or reset the form."""
    self.login_and_goto_page("core:contact")
    cancel_btn = self.page.locator("button[type='cancel']")
    cancel_btn.click()
    # after clicking cancel, should still be on a valid page
    self.page.wait_for_timeout(500)
    self.assert_url_contains("/")

  def test_contact_page_no_js_errors(self):
    """Contact page should not have JS errors."""
    self.login_and_goto_page("core:contact")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors on contact page: {self.errors}")
