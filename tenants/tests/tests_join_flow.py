from django.urls import reverse

# Template-aware variant: also recomputes the settings memoized for templates,
# so flipping MULTI_TENANT_ENABLED in a test is actually visible in rendering.
from core.context_processors import override_settings

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
    self.assertContains(response, self.tenant.name)
    self.assertEqual(response.context["settings"]["SITE_NAME"], "Famille Dubois")

  def test_join_link_visible_on_family_home_only(self):
    self.client.logout()
    family = self.client.get(reverse("tenant-home", args=["famille-dubois"]))
    self.assertContains(family, reverse("tenant-join", args=["famille-dubois"]))
    global_login = self.client.get(reverse("members:login"))
    self.assertNotContains(global_login, reverse("tenant-join", args=["famille-dubois"]))

  def test_join_page_title_uses_family_site_name(self):
    # The {% title %} tag reads the global settings.SITE_NAME; the join page
    # must use the tenant-layered value from the context processor instead.
    self.client.logout()
    response = self.client.get(reverse("tenant-join", args=["famille-dubois"]))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "<title>Famille Dubois - ")

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


class ReservedSlugTests(MemberTestCase):
  def test_reserved_slug_rejected(self):
    from django.forms import ValidationError

    from ..forms import uniquify_tenant_slug

    # "Chat & Galleries" slugifies to "chat-galleries", which is NOT reserved:
    # the tenant-home catch-all only matches a single path segment, so only an
    # exact slug can shadow a root route.
    for name in ("Members", "Accounts", "Chat", "Galleries", "Contact", "Pages", "Password reset"):
      with self.subTest(name=name):
        with self.assertRaises(ValidationError):
          uniquify_tenant_slug(name)

  def test_compound_slug_allowed(self):
    from ..forms import uniquify_tenant_slug

    self.assertEqual(uniquify_tenant_slug("Chat & Galleries"), "chat-galleries")

  def test_reserved_slugs_cover_root_routes(self):
    import re

    from ..forms import RESERVED_TENANT_SLUGS
    from cousinsmatter import urls as root_urls

    def first_segment(route):
      return route.split("/")[0]

    def slug_legal(segment):
      # Tenant.slug is a SlugField: letters/digits/underscore/hyphen only.
      return bool(segment) and "<" not in segment and re.fullmatch(r"[\w-]+", segment)

    def walk(patterns):
      for p in patterns:
        segment = first_segment(str(p.pattern))
        if slug_legal(segment):
          yield segment
        elif segment == "" and hasattr(p, "url_patterns"):
          # include("") mounts its children at the root
          yield from walk(p.url_patterns)

    covered = set(walk(root_urls.urlpatterns))
    self.assertIn("members", covered)
    self.assertIn("protected_media", covered)
    for slug in covered:
      with self.subTest(slug=slug):
        self.assertIn(slug, RESERVED_TENANT_SLUGS)
    # the tenant catch-alls are converters, skipped by the same rule
    self.assertFalse(slug_legal(first_segment("<slug:slug>/join/")))
    self.assertFalse(slug_legal(first_segment("<slug:slug>/")))


@override_settings(MULTI_TENANT_ENABLED=False)
class TenantHomeFlagOffTests(MemberTestCase):
  def test_default_tenant_home_works(self):
    response = self.client.get(reverse("tenant-home", args=[Tenant.get_default().slug]))
    self.assertEqual(response.status_code, 200)

  def test_other_tenant_slug_404(self):
    tenant = Tenant.objects.create(name="Other", slug="other")
    response = self.client.get(reverse("tenant-home", args=[tenant.slug]))
    self.assertEqual(response.status_code, 404)
