import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from members.models import Member
from tenants.models import Tenant, TenantSettings

from .base import _PWD, SaasUITestBase


class JoinFlowUITest(SaasUITestBase):
  """The signed-link flow: confirmation, site creation, welcome password screen."""

  def test_validate_link_shows_confirmation(self):
    """GET on the signed link shows the confirmation and creates nothing."""
    tr = self.make_tenant_request()
    self.page.goto(self.url(self.validate_link_path(tr)))
    self.assert_visible("h1.title.is-3", "Confirmation title should be visible")
    self.assertIn("Smith", self.page.content(), "Tenant name should be displayed")
    self.assert_visible("a[href*='/saas/signup/']", "Cancel link should be present")
    self.assertFalse(Tenant.objects.filter(slug="smith").exists(), "GET must not create the tenant")

  def test_confirm_creates_tenant_and_lands_on_welcome(self):
    """Confirming creates tenant, settings and admin member, then shows welcome."""
    tr = self.make_tenant_request()
    self.page.goto(self.url(self.validate_link_path(tr)))
    self.page.click("button[type='submit']")
    # click() only waits for the navigation commit: wait for the welcome page itself
    self.page.wait_for_selector("#id_new_password1", state="visible")
    self.assert_url_contains("/saas/welcome/", "Should land on the welcome screen")
    tenant = Tenant.objects.get(slug="smith")
    self.assertTrue(TenantSettings.objects.filter(tenant=tenant).exists(), "TenantSettings should exist")
    admin = Member.unscoped.get(email="founder@example.com")
    self.assertEqual(admin.tenant_id, tenant.pk, "Admin member should belong to the new tenant")
    self.assertEqual(admin.role, Member.Role.ADMIN, "Member should have the ADMIN role")
    tr.refresh_from_db()
    self.assertTrue(tr.is_validated, "The request should be validated")

  def test_welcome_set_password_reaches_home(self):
    """Setting the password on welcome redirects home with a success flash."""
    tr = self.make_tenant_request()
    self.page.goto(self.url(self.validate_link_path(tr)))
    self.page.click("button[type='submit']")
    self.page.fill("#id_new_password1", _PWD)
    self.page.fill("#id_new_password2", _PWD)
    self.page.click("button[type='submit']")
    self.page.wait_for_selector(".message.is-success", state="visible")
    self.assert_url_not_contains("/saas/welcome/", "Should be redirected to the app home")

  def test_welcome_skips_when_password_set(self):
    """Members who already have a password never see the welcome screen."""
    _tenant, admin = self.make_tenant_admin()
    self.login_as(admin, _PWD)
    self.goto_page("saas:welcome")
    self.assert_url_not_contains("/saas/welcome/", "Should be redirected away from welcome")
