import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from members.models import Member
from tenants.models import TenantSettings

from .base import _PWD, SaasUITestBase


class OnboardingUITest(SaasUITestBase):
  """The onboarding checklist rendered on every page for a fresh tenant admin."""

  def setUp(self):
    super().setUp()
    self.tenant, self.admin = self.make_tenant_admin()

  def _goto_home_as_admin(self):
    self.login_as(self.admin, _PWD)
    self.goto_page("core:Home")

  def test_checklist_visible_for_tenant_admin(self):
    """A fresh tenant admin sees the checklist: 2 steps done, 1 to do."""
    self._goto_home_as_admin()
    self.assert_visible("#saas-onboarding", "Checklist should be visible")
    self.assertEqual(
      self.page.locator("#saas-onboarding .has-background-success-light").count(),
      2,
      "Password and profile steps should show as done",
    )
    self.assertEqual(
      self.page.locator("#saas-onboarding .has-background-warning-light").count(),
      1,
      "Invite step should show as to do",
    )

  def test_checklist_all_done_when_member_joined(self):
    """Once another member joined, all 3 steps show as done."""
    Member.unscoped.create(username="cousin", email="cousin@example.com", tenant=self.tenant)
    self._goto_home_as_admin()
    self.assertEqual(
      self.page.locator("#saas-onboarding .has-background-success-light").count(),
      3,
      "All steps should show as done",
    )

  def test_dismiss_hides_checklist(self):
    """Dismiss posts to saas:onboarding_dismiss and hides the checklist."""
    self._goto_home_as_admin()
    self.page.click("#saas-onboarding form button[type='submit']")
    self.assert_url_not_contains("/saas/onboarding/", "Should redirect back home")
    self.assert_hidden("#saas-onboarding", "Checklist should be hidden after dismiss")
    overrides = TenantSettings.objects.get(tenant=self.tenant).overrides
    self.assertTrue(overrides.get("saas_onboarding_done"), "Dismiss flag should be stored")

  def test_checklist_hidden_for_regular_member(self):
    """Non-admin members never see the checklist."""
    cousin = Member.unscoped.create(username="cousin", email="cousin@example.com", tenant=self.tenant)
    cousin.set_password(_PWD)
    cousin.save()
    self.login_as(cousin, _PWD)
    self.goto_page("core:Home")
    self.assert_hidden("#saas-onboarding", "Checklist should be hidden for regular members")
