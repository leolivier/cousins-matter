"""Signed-link validation tests: tenant + admin creation, expiry, replay."""

from datetime import timedelta

from django.contrib.auth import get_user
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from members.models import Member
from tenants.models import Tenant, TenantSettings

from ..models import TenantRequest
from ..services import create_tenant_request
from ..tokens import TenantRequestTokenManager
from .utils import skip_if_saas_off


class ValidateTestsBase(TestCase):
  def setUp(self):
    skip_if_saas_off(self)

  def _make_request(self, email="founder@example.com", name="Smith", **kwargs):
    return create_tenant_request(email=email, tenant_name=name, **kwargs)

  def _link_path(self, tenant_request):
    request = RequestFactory().get("/")
    link = TenantRequestTokenManager().generate_link(request, tenant_request)
    return link.replace("http://testserver", "")


class ValidateTests(ValidateTestsBase):
  def test_link_creates_tenant_settings_admin_and_logs_in(self):
    tr = self._make_request()
    resp = self.client.get(self._link_path(tr))
    self.assertRedirects(resp, reverse("saas:welcome"), fetch_redirect_response=False)

    tenant = Tenant.objects.get(slug="smith")
    self.assertEqual(tenant.name, "Smith")
    self.assertTrue(TenantSettings.objects.filter(tenant=tenant).exists())
    member = Member.unscoped.get(email="founder@example.com")
    self.assertEqual(member.tenant_id, tenant.pk)
    self.assertEqual(member.role, Member.Role.ADMIN)
    self.assertTrue(member.is_active)
    self.assertFalse(member.has_usable_password())
    self.assertEqual(get_user(self.client), member)
    tr.refresh_from_db()
    self.assertTrue(tr.is_validated)
    self.assertIsNotNone(tr.validated_at)

  def test_slug_suffixed_on_collision(self):
    Tenant.objects.create(name="Smith", slug="smith")
    tr = self._make_request()
    self.client.get(self._link_path(tr))
    self.assertTrue(Tenant.objects.filter(slug="smith-2").exists())

  def test_expired_link_refused(self):
    tr = self._make_request()
    TenantRequest.objects.filter(pk=tr.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
    resp = self.client.get(self._link_path(tr))
    self.assertRedirects(resp, reverse("saas:signup"))
    tr.refresh_from_db()
    self.assertTrue(tr.is_expired)
    self.assertFalse(Tenant.objects.filter(slug="smith").exists())

  def test_replayed_link_refused(self):
    tr = self._make_request()
    path = self._link_path(tr)
    self.client.get(path)
    self.assertEqual(Tenant.objects.filter(slug="smith").count(), 1)
    resp = self.client.get(path)
    self.assertRedirects(resp, reverse("saas:signup"))
    self.assertEqual(Tenant.objects.filter(slug="smith").count(), 1)

  def test_tampered_link_refused(self):
    tr = self._make_request()
    path = self._link_path(tr)
    bad = path[:-3] + "xyz/"
    resp = self.client.get(bad)
    self.assertRedirects(resp, reverse("saas:signup"))
    self.assertFalse(Tenant.objects.exclude(slug__in=["default", "system"]).exists())
