"""Onboarding checklist tests: visibility rules + dismiss."""

from django.test import TestCase
from django.urls import reverse

from members.models import Member
from pages.services import seed_tenant_pages
from tenants.models import Tenant, TenantSettings

from .utils import skip_if_saas_off

_PWD = "pw-12345-Aa"


def _make_admin(email="admin@example.com", password=True):
  tenant = Tenant.objects.create(name="Smith", slug="smith")
  TenantSettings.objects.create(tenant=tenant)
  # the home page includes the tenant's own copy of the predefined pages
  seed_tenant_pages(tenant)
  admin = Member.unscoped.create(
    username="admin",
    email=email,
    tenant=tenant,
    role=Member.Role.ADMIN,
    first_name="Joe",
    last_name="Smith",
  )
  if password:
    admin.set_password(_PWD)
  else:
    admin.set_unusable_password()
  admin.save()
  return tenant, admin


class OnboardingTests(TestCase):
  def setUp(self):
    skip_if_saas_off(self)
    self.tenant, self.admin = _make_admin()

  def test_checklist_shown_to_tenant_admin(self):
    self.client.force_login(self.admin)
    resp = self.client.get("/")
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "saas-onboarding")
    # fresh admin: password + profile + invite all to do
    self.assertContains(resp, "Dismiss")

  def test_checklist_marks_done_steps(self):
    Member.unscoped.create(username="cousin", email="cousin@example.com", tenant=self.tenant)
    self.client.force_login(self.admin)
    resp = self.client.get("/")
    self.assertEqual(resp.status_code, 200)
    # all 3 steps done (password set, profile filled, a member joined)
    self.assertEqual(resp.content.decode().count("has-background-success-light"), 3)

  def test_checklist_hidden_for_regular_member(self):
    member = Member.unscoped.create(username="cousin", email="cousin@example.com", tenant=self.tenant)
    self.client.force_login(member)
    resp = self.client.get("/")
    self.assertEqual(resp.status_code, 200)
    self.assertNotContains(resp, "saas-onboarding")

  def test_dismiss_hides_checklist(self):
    self.client.force_login(self.admin)
    resp = self.client.post(reverse("saas:onboarding_dismiss"))
    self.assertEqual(resp.status_code, 302)
    overrides = TenantSettings.objects.get(tenant=self.tenant).overrides
    self.assertTrue(overrides.get("saas_onboarding_done"))
    resp = self.client.get("/")
    self.assertNotContains(resp, "saas-onboarding")
