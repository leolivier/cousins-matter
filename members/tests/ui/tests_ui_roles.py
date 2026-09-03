"""UI tests exercising the three role levels on the same pages:

* the **platform superuser** (``is_superuser``, unscoped, Django-admin staff),
* the **tenant admin** (``Member.role="admin"`` of the default tenant),
* a **regular member**.

They assert the navbar admin entries and the member-edit permissions differ
per role. Runs with the default settings (MULTI_TENANT_ENABLED off) so the
multi-tenant entries are absent for everyone — the flag-on variants live in
tenants/tests/tests_feature_on.py.
"""

import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.urls import reverse

from core.tests.ui import PlaywrightTestCase
from members.models import Member
from members.tests.factories import MemberFactory
from tenants.scoping import set_current_tenant


class RoleAwareUITestBase(PlaywrightTestCase):
  """Creates the three roles on the (default) tenant; self.user is the superuser."""

  def setUp(self):
    super().setUp()
    set_current_tenant(None)
    self.tenant_admin = MemberFactory(
      username="tenant-admin",
      email="tenant-admin@example.com",
      first_name="Tania",
      last_name="Admin",
      is_active=True,
      role=Member.Role.ADMIN,
    )
    self.tenant_admin.set_password("password")
    self.tenant_admin.save()
    self.regular_member = MemberFactory(
      username="plain-member",
      email="plain-member@example.com",
      first_name="Paul",
      last_name="Member",
      is_active=True,
    )
    self.regular_member.set_password("password")
    self.regular_member.save()

  def tearDown(self):
    set_current_tenant(None)
    super().tearDown()

  # -- helpers ------------------------------------------------------- #

  def login_as_tenant_admin(self):
    self.login_as(self.tenant_admin)

  def login_as_regular_member(self):
    self.login_as(self.regular_member)

  def admin_entries(self) -> dict[str, bool]:
    """Visibility of the navbar admin-dropdown entries (scoped to the navbar:
    the home flatpage body also links to /pages-edit/admin for everyone)."""
    navbar = self.page.locator("nav.navbar")
    return {
      "edit_pages": navbar.locator("a[href='/pages-edit/admin']").count() > 0,
      "import_members": navbar.locator("a[href='/members/import']").count() > 0,
      "admin_site": navbar.locator("a[href='/admin']").count() > 0,
      "manage_families": navbar.locator("a[href*='/tenants/']").count() > 0,
    }


class NavbarRolesUITest(RoleAwareUITestBase):
  """The admin dropdown shows entries per role."""

  def test_superuser_navbar(self):
    self.login_as_admin()
    self.page.goto(self.url("/"))
    entries = self.admin_entries()
    self.assertTrue(entries["edit_pages"])
    self.assertTrue(entries["import_members"])
    self.assertTrue(entries["admin_site"], "superuser must see the Django admin link")
    self.assertFalse(entries["manage_families"], "multi-tenant entries hidden when the flag is off")

  def test_tenant_admin_navbar(self):
    self.login_as_tenant_admin()
    self.page.goto(self.url("/"))
    entries = self.admin_entries()
    self.assertTrue(entries["edit_pages"], "tenant admin keeps the site-admin entries")
    self.assertTrue(entries["import_members"])
    self.assertFalse(entries["admin_site"], "tenant admins are not staff: no Django admin link")
    self.assertFalse(entries["manage_families"])

  def test_regular_member_navbar(self):
    self.login_as_regular_member()
    self.page.goto(self.url("/"))
    entries = self.admin_entries()
    self.assertFalse(entries["edit_pages"])
    self.assertFalse(entries["import_members"])
    self.assertFalse(entries["admin_site"])
    self.assertFalse(entries["manage_families"])

  def test_regular_member_cannot_reach_django_admin(self):
    self.login_as_regular_member()
    self.page.goto(self.url("/admin/"))
    # non-staff is bounced to the login page
    self.assert_url_contains("/login/")


class MemberEditRolesUITest(RoleAwareUITestBase):
  """Editing another member depends on the role."""

  def _edit_url(self) -> str:
    return self.url(reverse("members:member_edit", kwargs={"username": self.regular_member.username}))

  def test_superuser_can_edit_any_member(self):
    self.login_as_admin()
    self.page.goto(self._edit_url())
    self.assert_visible("input[name='first_name']", "superuser must reach the member edit form")

  def test_tenant_admin_can_edit_member_of_own_tenant(self):
    self.login_as_tenant_admin()
    self.page.goto(self._edit_url())
    self.assert_visible("input[name='first_name']", "tenant admin must reach the member edit form")

  def test_regular_member_cannot_edit_other_member(self):
    # Create an extra member
    self.other_member = MemberFactory(
      username="othermember",
      first_name="Other",
      last_name="Member",
      birthdate="1990-01-01",
    )

    self.login_as_regular_member()
    other_member_url = self.url(reverse("members:member_edit", kwargs={"username": self.other_member.username}))
    self.page.goto(other_member_url)
    # bounced back to the member detail page with an error message
    self.assert_url_not_contains("/edit")

  def test_member_can_edit_own_profile(self):
    self.login_as_regular_member()
    self.page.goto(self.url(reverse("members:profile")))
    self.assert_visible("input[name='first_name']", "a member must reach their own profile form")
