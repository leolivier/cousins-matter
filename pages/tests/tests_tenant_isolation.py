"""Tenant-isolation tests pages (TenantModel).

Proves ``pages.FlatPage`` (MTI child of ``django.contrib.flatpages``'
model) honors the tenant-scoped manager, that two tenants can own the
same page URL (the global ``django_flatpage`` unique dropped in
``pages.0004_tenant``), ``unscoped`` escape hatch, default-tenant
fallback, and that ``seed_tenant_pages`` gives each family its own
copy of the predefined pages.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import get_language

from pages.forms import AdminPageForm
from pages.models import FlatPage
from pages.services import seed_tenant_pages
from pages.tests.factories import FlatPageFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context

Member = get_user_model()

_PWD = "pw-12345-Aa"


def _make_admin(tenant, username):
  with tenant_context(tenant):
    return Member.objects.create_member(
      username=username,
      email=f"{username}@example.com",
      password=_PWD,
      first_name=username,
      last_name="x",
      is_active=True,
      role=Member.Role.ADMIN,
      privacy_consent=True,  # these tests exercise tenant isolation, not the consent gate
    )


class PagesTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-pages-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-pages-b")
    cls.page_a = FlatPageFactory(tenant=cls.tenant_a, url="/home/authenticated/")
    cls.page_b = FlatPageFactory(tenant=cls.tenant_b, url="/home/authenticated/")

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      self.assertNotIn(self.page_b.id, set(FlatPage.objects.values_list("id", flat=True)))
      # tenant_a sees its own page (plus the fixture pages seeded on creation),
      # never tenant_b's
      self.assertIn("/home/authenticated/", set(FlatPage.objects.values_list("url", flat=True)))
    with tenant_context(self.tenant_b):
      self.assertNotIn(self.page_a.id, set(FlatPage.objects.values_list("id", flat=True)))

  def test_same_url_in_two_tenants(self):
    # the global django_flatpage unique is gone; both rows coexist
    self.assertEqual(self.page_a.url, self.page_b.url)
    self.assertNotEqual(self.page_a.id, self.page_b.id)

  def test_unscoped(self):
    unscoped = set(FlatPage.unscoped.values_list("id", flat=True))
    self.assertIn(self.page_a.id, unscoped)
    self.assertIn(self.page_b.id, unscoped)

  def _admin_form_data(self, page):
    return {
      "url": page.url,
      "title": page.title,
      "content": page.content,
      "template_name": page.template_name,
      "registration_required": page.registration_required,
      "sites": [settings.SITE_ID],
    }

  def test_admin_form_update_ignores_other_tenants_copy(self):
    # page_b (other tenant) owns the same URL on the same site: the stock
    # FlatpageForm rejected the update with "already exists for site"
    form = AdminPageForm(instance=self.page_a, data=self._admin_form_data(self.page_a))
    self.assertTrue(form.is_valid(), form.errors)

  def test_admin_form_still_blocks_same_tenant_duplicate(self):
    FlatPageFactory(tenant=self.tenant_a, url=self.page_a.url)
    form = AdminPageForm(instance=self.page_a, data=self._admin_form_data(self.page_a))
    self.assertFalse(form.is_valid())
    self.assertEqual([e.code for e in form.non_field_errors().as_data()], ["duplicate_url"])

  def test_save_without_tenant_falls_back_to_default(self):
    page = FlatPageFactory.build(tenant=None)
    page.save()
    self.assertEqual(page.tenant.slug, Tenant.get_default().slug)

  def test_seed_tenant_pages_copies_predefined_pages(self):
    tenant = Tenant.objects.create(name="C", slug="t-pages-c")
    # the post_save signal already seeded the tenant; start from a clean
    # slate to unit-test the seeding function itself
    FlatPage.unscoped.filter(tenant=tenant).delete()
    count = seed_tenant_pages(tenant)
    self.assertEqual(count, FlatPage.unscoped.filter(tenant=tenant).count())
    self.assertGreater(count, 0)
    with tenant_context(tenant):
      seeded = FlatPage.objects.filter(url="/fr/home/authenticated/").first()
    self.assertIsNotNone(seeded)
    self.assertTrue(seeded.predefined)
    self.assertFalse(seeded.updated)
    # default tenant's own copy is untouched (separate rows, same URL)
    self.assertNotEqual(seeded.id, FlatPage.unscoped.get(tenant=Tenant.get_default(), url="/fr/home/authenticated/").id)

  def test_seed_tenant_pages_is_idempotent(self):
    tenant = Tenant.objects.create(name="D", slug="t-pages-d")
    count = FlatPage.unscoped.filter(tenant=tenant).count()
    # re-seeding neither duplicates pages nor overwrites UI edits
    page = FlatPage.unscoped.get(tenant=tenant, url="/fr/home/authenticated/")
    page.updated = True
    page.content = "<p>edited</p>"
    page.save()
    self.assertEqual(seed_tenant_pages(tenant), count)
    page.refresh_from_db()
    self.assertEqual(page.content, "<p>edited</p>")
    # deleted pages are re-created
    FlatPage.unscoped.get(tenant=tenant, url="/fr/about/privacy-policy/").delete()
    seed_tenant_pages(tenant)
    self.assertEqual(FlatPage.unscoped.filter(tenant=tenant).count(), count)
    self.assertTrue(FlatPage.unscoped.filter(tenant=tenant, url="/fr/about/privacy-policy/").exists())


class PagesViewsTenantIsolationTests(TestCase):
  """HTTP-level isolation for the edit views.

  The list views must build their queryset per request (a class-level
  ``queryset`` attribute is frozen at import time, when no tenant is
  active), and ``PageUpdateView`` must let a tenant admin update their
  own pages while returning 404 on another tenant's page.
  """

  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="VA", slug="t-pages-views-a")
    cls.tenant_b = Tenant.objects.create(name="VB", slug="t-pages-views-b")
    cls.admin_a = _make_admin(cls.tenant_a, "pages_admin_a")
    with tenant_context(cls.tenant_a):
      cls.page_a = FlatPageFactory(tenant=cls.tenant_a, url="/home/authenticated/")
    with tenant_context(cls.tenant_b):
      cls.page_b = FlatPageFactory(tenant=cls.tenant_b, url="/home/authenticated/")

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_list_views_scoped_to_own_tenant(self):
    self.client.force_login(self.admin_a)
    for url_name in ("pages-edit:edit_list", "pages-edit:tree"):
      resp = self.client.get(reverse(url_name))
      self.assertEqual(resp.status_code, 200)
      shown = set(resp.context["object_list"].values_list("pk", flat=True))
      with tenant_context(self.tenant_a):
        own = set(FlatPage.objects.values_list("pk", flat=True))
      self.assertEqual(shown, own)
      self.assertNotIn(self.page_b.pk, shown)

  def test_tenant_admin_updates_own_page(self):
    self.client.force_login(self.admin_a)
    data = {"url": self.page_a.url, "title": "Updated", "content": "<p>x</p>", "save": "true"}
    resp = self.client.post(reverse("pages-edit:update", args=[self.page_a.pk]), data)
    self.assertEqual(resp.status_code, 302)
    self.page_a.refresh_from_db()
    self.assertTrue(self.page_a.updated)
    self.assertEqual(self.page_a.title, "Updated")

  def test_tenant_admin_cannot_update_other_tenant_page(self):
    self.client.force_login(self.admin_a)
    data = {"url": self.page_b.url, "title": "Hijack", "content": "x", "save": "true"}
    resp = self.client.post(reverse("pages-edit:update", args=[self.page_b.pk]), data)
    self.assertEqual(resp.status_code, 404)


class AnonymousPublicPagesScopingTests(TestCase):
  """Anonymous and superuser requests are deliberately unscoped (allauth
  must resolve users by email; platform admins see every tenant), so the
  public flatpage lookups must scope themselves to the default tenant —
  never serve or list another family's copy.

  Regression: on the site root (include_page, navbar/footer page lists)
  unscoped lookups served an arbitrary tenant's page, and on
  ``/pages/<url>`` (also reachable by the fallback middleware) they
  crashed with MultipleObjectsReturned when two tenants owned the same
  URL.
  """

  @classmethod
  def setUpTestData(cls):
    cls.default = Tenant.get_default()
    cls.other = Tenant.objects.create(name="Anon Other", slug="t-anon-other")
    cls.superuser = Member.objects.create_member(
      username="anon_super",
      email="anon_super@example.com",
      password=_PWD,
      first_name="anon_super",
      last_name="x",
      is_active=True,
      is_superuser=True,
      privacy_consent=True,  # otherwise the consent gate (PR #521) 302s to the profile
    )
    cls.default_page = FlatPageFactory(
      tenant=cls.default,
      url="/anon-scope-test/",
      content="<p>DEFAULT-ANON-CONTENT</p>",
    )
    cls.other_page = FlatPageFactory(
      tenant=cls.other,
      url="/anon-scope-test/",
      content="<p>OTHER-ANON-CONTENT</p>",
    )

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_unscoped_request_flatpage_serves_default_tenant_copy(self):
    # anonymous users are redirected to login before reaching the view
    # (login-required-by-default), so exercise the unscoped path with a
    # platform superuser: TenantMiddleware leaves them tenantless, the
    # lookups must fall back to the default tenant's copy instead of
    # crashing on MultipleObjectsReturned (same URL in two tenants)
    self.client.force_login(self.superuser)
    resp = self.client.get("/pages/anon-scope-test/")
    self.assertContains(resp, "DEFAULT-ANON-CONTENT")
    self.assertNotContains(resp, "OTHER-ANON-CONTENT")

  def test_anonymous_home_shows_default_tenant_page_content(self):
    # both tenants own the seeded unauthenticated home page; make the
    # other family's copy distinctive and prove the root home never
    # serves it through include_page
    other_home = FlatPage.unscoped.get(tenant=self.other, url=f"/{get_language()}/home/unauthenticated/")
    other_home.content = "OTHER-ANON-HOME-CONTENT"
    other_home.save()
    default_home = FlatPage.unscoped.get(tenant=self.default, url=f"/{get_language()}/home/unauthenticated/")
    resp = self.client.get("/")
    self.assertContains(resp, default_home.content)
    self.assertNotContains(resp, "OTHER-ANON-HOME-CONTENT")

  def test_anonymous_navbar_does_not_list_other_tenant_pages(self):
    FlatPageFactory(
      tenant=self.other,
      url=f"/{get_language()}/about/other-family-page/",
      title="OTHER-FAMILY-PAGE-TITLE",
    )
    resp = self.client.get("/")
    self.assertNotContains(resp, "OTHER-FAMILY-PAGE-TITLE")
