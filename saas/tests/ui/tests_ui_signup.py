import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from members.models import Member
from saas.models import TenantRequest

from .base import SaasUITestBase


class SignupFormUITest(SaasUITestBase):
  """The public signup form: display, validation errors, success screen."""

  def test_signup_form_display(self):
    """The signup form shows both fields, a hidden CSRF token and a submit button."""
    self.goto_page("saas:signup")
    self.assert_visible("legend.title.is-3", "Form legend should be visible")
    self.assert_visible("#id_tenant_name", "Family name field should be visible")
    self.assert_visible("#id_email", "Email field should be visible")
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    # the CSRF token is a hidden input (and the navbar form carries its own): check presence
    self.assertEqual(
      self.page.locator(".box form input[name='csrfmiddlewaretoken']").count(),
      1,
      "CSRF token should be present in the page's own form",
    )

  def test_signup_member_email_shows_errors(self):
    """An email already used by a member re-renders the form with an error."""
    Member.unscoped.create(username="founder", email="founder@example.com")
    self.goto_page("saas:signup")
    self.page.fill("#id_tenant_name", "Smith")
    self.page.fill("#id_email", "founder@example.com")
    self.page.click("button[type='submit']")
    # crispy-bulma renders field errors as <p class="help is-danger">
    self.page.wait_for_selector(".help.is-danger", state="visible")
    self.assert_url_not_contains("/saas/signup/sent/", "Should not reach the sent page")

  def test_signup_valid_request_shows_sent_page(self):
    """A valid submission lands on the 'check your mailbox' screen."""
    self.goto_page("saas:signup")
    self.page.fill("#id_tenant_name", "Smith")
    self.page.fill("#id_email", "founder@example.com")
    self.page.click("button[type='submit']")
    # click() only waits for the navigation commit: wait for the sent page itself
    self.page.wait_for_selector("h1.title.is-3", state="visible")
    self.assert_url_contains("/saas/signup/sent/", "Should land on the sent page")
    self.assert_visible(".box a[href*='/saas/signup/']", "A link back to the form should be present")
    tr = TenantRequest.objects.get(email="founder@example.com")
    self.assertTrue(tr.is_pending, "The tenant request should be pending")
