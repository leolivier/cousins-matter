"""Tenant-isolation tests for the shared-schema multi-tenant layer.

Proves the boundaries the architecture depends on:

* the tenant-scoped manager keeps one tenant's members invisible to another;
* the ``unscoped`` escape hatch and ``tenant_context()`` work as intended;
* new members land on the active tenant;
* cross-tenant HTTP access (detail/list/edit) is blocked;
* the per-tenant admin role behaves and cannot create tenants;
* a deactivated tenant blocks login.

These tests are self-contained (they create their own tenants/members under
explicit ``tenant_context``) so they do not depend on the wider test-suite
adaptation (``MemberTestCase`` ``force_login``/role rework, fixtures).
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context

Member = get_user_model()

_PWD = "pw-12345-Aa"


def _make_member(tenant, username, *, role=Member.Role.MEMBER, is_active=True):
  with tenant_context(tenant):
    # NOTE: do NOT overwrite m.password after creation — force_login() derives
    # the session auth hash from user.password, so a plaintext value would
    # mismatch the DB hash and silently log the user out on the next request.
    return Member.objects.create_member(
      username=username,
      password=_PWD,
      email=f"{username}@example.com",
      first_name=username,
      last_name="x",
      is_active=is_active,
      role=role,
    )


class TenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="Tenant A", slug="m-tenant-a")
    cls.tenant_b = Tenant.objects.create(name="Tenant B", slug="m-tenant-b")
    cls.admin_a = _make_member(cls.tenant_a, "admin_a", role=Member.Role.ADMIN)
    cls.member_a = _make_member(cls.tenant_a, "member_a")
    cls.admin_b = _make_member(cls.tenant_b, "admin_b", role=Member.Role.ADMIN)
    cls.member_b = _make_member(cls.tenant_b, "member_b")

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  # --- ORM-level isolation ---
  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      names = set(Member.objects.filter(is_superuser=False).values_list("username", flat=True))
    self.assertIn("member_a", names)
    self.assertIn("admin_a", names)
    self.assertNotIn("member_b", names)
    self.assertNotIn("admin_b", names)

  def test_no_active_tenant_is_unfiltered(self):
    # management commands / no request -> manager is unfiltered (auth, migrations)
    names = set(Member.objects.filter(is_superuser=False).values_list("username", flat=True))
    self.assertIn("member_a", names)
    self.assertIn("member_b", names)

  def test_unscoped_escape_hatch(self):
    everyone = set(Member.unscoped.filter(is_superuser=False).values_list("username", flat=True))
    self.assertEqual(everyone, {"admin_a", "member_a", "admin_b", "member_b"})

  def test_create_member_lands_on_active_tenant(self):
    with tenant_context(self.tenant_b):
      m = Member.objects.create_member(
        username="new_b",
        password=_PWD,
        email="new_b@example.com",
        first_name="new",
        last_name="b",
        is_active=True,
      )
    self.assertEqual(m.tenant_id, self.tenant_b.id)
    with tenant_context(self.tenant_a):
      self.assertFalse(Member.objects.filter(username="new_b").exists())
    with tenant_context(self.tenant_b):
      self.assertTrue(Member.objects.filter(username="new_b").exists())

  def test_username_reuse_across_tenants(self):
    # (tenant, username) is unique, not username alone
    with tenant_context(self.tenant_b):
      m = Member.objects.create_member(
        username="member_a",  # same username as tenant A's member
        password=_PWD,
        email="member_a_reused@example.com",
        first_name="dup",
        last_name="b",
        is_active=True,
      )
    self.assertEqual(m.tenant_id, self.tenant_b.id)

  # --- HTTP-level isolation ---
  def test_tenant_admin_lists_only_own_tenant(self):
    self.client.force_login(self.admin_a)
    resp = self.client.get(reverse("members:members"))
    self.assertContains(resp, self.member_a.username)
    self.assertNotContains(resp, self.member_b.username)

  def test_cross_tenant_detail_is_404(self):
    self.client.force_login(self.admin_a)
    resp = self.client.get(reverse("members:detail", args=[self.member_b.username]))
    self.assertEqual(resp.status_code, 404)

  def test_cross_tenant_edit_blocked(self):
    self.client.force_login(self.admin_a)
    resp = self.client.get(reverse("members:member_edit", args=[self.member_b.username]))
    self.assertIn(resp.status_code, (403, 404))


class TenantAdminRoleTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant = Tenant.objects.create(name="Role Tenant", slug="role-tenant")
    cls.admin = _make_member(cls.tenant, "role_admin", role=Member.Role.ADMIN)
    cls.member = _make_member(cls.tenant, "role_member", role=Member.Role.MEMBER)

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_is_tenant_admin_property(self):
    self.assertTrue(self.admin.is_tenant_admin)
    self.assertFalse(self.member.is_tenant_admin)

  def test_tenant_admin_is_not_platform_admin(self):
    # tenant creation / Django admin are gated to platform superusers (is_staff)
    self.assertFalse(self.admin.is_superuser)
    self.assertFalse(self.admin.is_staff)


class InactiveTenantTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant = Tenant.objects.create(name="Doomed", slug="inactive-tenant")
    cls.member = _make_member(cls.tenant, "doomed_member")

  def setUp(self):
    set_current_tenant(None)

  def test_inactive_tenant_blocks_access(self):
    self.tenant.is_active = False
    self.tenant.save()
    self.client.force_login(self.member)
    resp = self.client.get(reverse("members:members"))
    # TenantMiddleware logs the user out and redirects to login
    self.assertEqual(resp.status_code, 302)
    self.assertIn(reverse("members:login"), resp["Location"])
    # the session no longer holds an authenticated user
    self.assertFalse(resp.wsgi_request.user.is_authenticated)


class DeleteTenantCommandTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant = Tenant.objects.create(name="Removable", slug="removable-tenant")
    cls.member = _make_member(cls.tenant, "removable_member")

  def test_refuses_system_tenant(self):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    with self.assertRaises(CommandError):
      call_command("delete_tenant", Tenant.get_system().slug)

  def test_refuses_active_tenant(self):
    from django.core.management import call_command
    from django.core.management.base import CommandError

    with self.assertRaises(CommandError):
      call_command("delete_tenant", "removable-tenant")

  def test_hard_deletes_inactive_tenant(self):
    from django.core.management import call_command

    self.tenant.is_active = False
    self.tenant.save()
    call_command("delete_tenant", "removable-tenant", yes=True)
    self.assertFalse(Tenant.objects.filter(slug="removable-tenant").exists())
    self.assertFalse(Member.unscoped.filter(username="removable_member").exists())
