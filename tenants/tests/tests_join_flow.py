from django.test import override_settings
from django.urls import reverse

from members.tests.tests_member_base import MemberTestCase

from ..models import Tenant, TenantSettings


class ResolveJoinTenantTests(MemberTestCase):
  """Unit tests for tenants.services.resolve_join_tenant."""

  def resolve(self, slug):
    from ..services import resolve_join_tenant

    return resolve_join_tenant(slug)

  def test_none_slug_resolves_default_tenant(self):
    self.assertEqual(self.resolve(None).pk, Tenant.get_default().pk)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_valid_slug_resolves_tenant(self):
    tenant = Tenant.objects.create(name="Famille Dubois", slug="famille-dubois")
    self.assertEqual(self.resolve("famille-dubois").pk, tenant.pk)

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_unknown_slug_is_none(self):
    self.assertIsNone(self.resolve("inconnu"))

  @override_settings(MULTI_TENANT_ENABLED=True)
  def test_inactive_tenant_is_none(self):
    tenant = Tenant.objects.create(name="Ghost", slug="ghost", is_active=False)
    self.assertIsNone(self.resolve(tenant.slug))

  @override_settings(MULTI_TENANT_ENABLED=False)
  def test_flag_off_other_slug_is_none(self):
    Tenant.objects.create(name="Other", slug="other")
    self.assertIsNone(self.resolve("other"))

  @override_settings(MULTI_TENANT_ENABLED=False)
  def test_flag_off_default_slug_resolves(self):
    self.assertEqual(self.resolve(Tenant.get_default().slug).pk, Tenant.get_default().pk)


@override_settings(MULTI_TENANT_ENABLED=True)
class TenantHomeTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.tenant = Tenant.objects.create(name="Famille Dubois", slug="famille-dubois")
    # Overrides keys are lowercase (TENANT_SETTINGS_SPEC) and the site logo is
    # the branding surface the login page actually renders.
    TenantSettings.objects.create(
      tenant=self.tenant,
      overrides={"site_name": "Famille Dubois", "site_logo": "tenants/images/famille-dubois.jpg"},
    )

  def test_home_renders_login_page_with_family_branding(self):
    self.client.logout()
    response = self.client.get(reverse("tenant-home", args=["famille-dubois"]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/login/login.html")
    self.assertContains(response, "famille-dubois.jpg")
    self.assertEqual(response.context["settings"]["SITE_NAME"], "Famille Dubois")

  def test_home_login_post_works(self):
    self.client.logout()
    response = self.client.post(
      reverse("tenant-home", args=["famille-dubois"]),
      {"username": self.superuser.username, "password": self.superuser.password},
      follow=True,
    )
    self.assertTrue(response.context["user"].is_authenticated)

  def test_unknown_slug_404(self):
    response = self.client.get(reverse("tenant-home", args=["inconnu"]))
    self.assertEqual(response.status_code, 404)

  def test_inactive_tenant_404(self):
    self.tenant.is_active = False
    self.tenant.save()
    response = self.client.get(reverse("tenant-home", args=["famille-dubois"]))
    self.assertEqual(response.status_code, 404)


@override_settings(MULTI_TENANT_ENABLED=False)
class TenantHomeFlagOffTests(MemberTestCase):
  def test_default_tenant_home_works(self):
    response = self.client.get(reverse("tenant-home", args=[Tenant.get_default().slug]))
    self.assertEqual(response.status_code, 200)

  def test_other_tenant_slug_404(self):
    tenant = Tenant.objects.create(name="Other", slug="other")
    response = self.client.get(reverse("tenant-home", args=[tenant.slug]))
    self.assertEqual(response.status_code, 404)
