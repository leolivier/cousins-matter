"""Family signup + management + settings tests (run with MULTI_TENANT_ENABLED=True).

These exercise the product feature end to end: self-service family creation,
the platform-admin management UI, and the per-family settings form.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from members.tests.tests_member_base import MemberTestCase
from tenants.forms import uniquify_tenant_slug
from tenants.models import Tenant, TenantSettings
from tenants.scoping import set_current_tenant, tenant_context

Member = get_user_model()

_PWD = "pw-12345-Aa"


# The URLconf only mounts /tenants/ when the flag was on at import; these tests
# require that (they are skipped otherwise, e.g. under the default settings).
def _skip_if_off(testcase):
  from django.conf import settings

  if not settings.MULTI_TENANT_ENABLED:
    testcase.skipTest("MULTI_TENANT_ENABLED is off in this environment")


def _make_admin(tenant, username):
  with tenant_context(tenant):
    m = Member.objects.create_member(
      username=username,
      password=_PWD,
      email=f"{username}@example.com",
      first_name=username,
      last_name="x",
      is_active=True,
      role=Member.Role.ADMIN,
    )
  return m


class FamilySignupTests(TestCase):
  def setUp(self):
    _skip_if_off(self)
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def _post_signup(self, name="Smith", username="founder", email="founder@example.com"):
    url = reverse("tenants:family_signup")
    data = {
      "name": name,
      "username": username,
      "email": email,
      "password1": _PWD,
      "password2": _PWD,
      "first_name": "Found",
      "last_name": "Er",
      "birthdate": "1990-01-01",
      "privacy_consent": "on",
      "email_batch_frequency": "immediate",
    }
    return self.client.post(url, data, follow=True)

  def test_signup_creates_tenant_and_admin(self):
    resp = self._post_signup()
    self.assertEqual(resp.status_code, 200)
    tenant = Tenant.objects.filter(slug="smith").first()
    self.assertIsNotNone(tenant)
    self.assertTrue(TenantSettings.objects.filter(tenant=tenant).exists())
    founder = Member.unscoped.filter(email="founder@example.com").first()
    self.assertIsNotNone(founder)
    self.assertEqual(founder.tenant_id, tenant.pk)
    self.assertEqual(founder.role, Member.Role.ADMIN)
    self.assertFalse(founder.is_active)  # pending email verification

  def test_duplicate_email_rejected_globally(self):
    # create an existing member on the default tenant
    from tenants.models import Tenant as T

    default = T.get_default()
    with tenant_context(default):
      Member.objects.create_member(
        username="taken",
        password=_PWD,
        email="founder@example.com",
        first_name="t",
        last_name="k",
        is_active=True,
      )
    before = Tenant.objects.filter(slug="smith").count()
    resp = self._post_signup()
    self.assertContains(resp, "already exists")
    self.assertEqual(Tenant.objects.filter(slug="smith").count(), before)

  def test_slug_uniquified(self):
    Tenant.objects.create(name="Smith", slug="smith")
    self._post_signup(name="Smith", username="founder2", email="f2@example.com")
    self.assertTrue(Tenant.objects.filter(slug="smith-2").exists())

  def test_reserved_slug_rejected(self):
    from tenants.forms import RESERVED_TENANT_SLUGS as R

    reserved = next(iter(R))
    self._post_signup(name=reserved.title(), username="x1", email="x1@example.com")
    # form re-renders with the error, nothing created
    self.assertEqual(Tenant.objects.exclude(slug__in=["default", "system"]).count(), 0)


class SlugHelperTests(TestCase):
  def test_uniquify_appends_suffix(self):
    Tenant.objects.create(name="A", slug="dup")
    self.assertEqual(uniquify_tenant_slug("Dup"), "dup-2")


class TenantManageTests(MemberTestCase):
  """Platform-admin lifecycle UI; tenant admins and members are refused."""

  def setUp(self):
    _skip_if_off(self)
    super().setUp()
    self.other = Tenant.objects.create(name="Other", slug="other-family")
    self.other_admin = _make_admin(self.other, "other_admin")

  def _login_superuser(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)

  def test_superuser_lists_tenants(self):
    self._login_superuser()
    resp = self.client.get(reverse("tenants:list"))
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "Other")

  def test_tenant_admin_refused(self):
    self.client.force_login(self.other_admin)
    for url in (reverse("tenants:list"), reverse("tenants:create")):
      resp = self.client.get(url)
      self.assertEqual(resp.status_code, 403, url)

  def test_anonymous_redirected_to_login(self):
    # MemberTestCase.setUp() logs in as the regular member: log out first
    self.client.logout()
    resp = self.client.get(reverse("tenants:list"))
    self.assertEqual(resp.status_code, 302)
    self.assertIn(reverse("members:login"), resp["Location"])

  def test_create_with_admin_invitation(self):
    self._login_superuser()
    resp = self.client.post(reverse("tenants:create"), {"name": "New Family", "admin_email": "first@example.com"}, follow=True)
    self.assertEqual(resp.status_code, 200)
    self.assertTrue(Tenant.objects.filter(slug="new-family").exists())

  def test_toggle_active_refuses_system(self):
    self._login_superuser()
    resp = self.client.post(reverse("tenants:toggle_active", args=["system"]), follow=True)
    self.assertContains(resp, "cannot be deactivated")

  def test_delete_requires_confirmation_and_inactive(self):
    self._login_superuser()
    # active -> refused
    resp = self.client.post(reverse("tenants:delete", args=["other-family"]), {"confirmation": "other-family"}, follow=True)
    self.assertContains(resp, "still active")
    self.assertTrue(Tenant.objects.filter(slug="other-family").exists())
    # deactivate then wrong confirmation -> refused
    self.other.is_active = False
    self.other.save()
    resp = self.client.post(reverse("tenants:delete", args=["other-family"]), {"confirmation": "nope"}, follow=True)
    self.assertContains(resp, "did not match")
    # correct confirmation -> deleted with members
    resp = self.client.post(reverse("tenants:delete", args=["other-family"]), {"confirmation": "other-family"}, follow=True)
    self.assertFalse(Tenant.objects.filter(slug="other-family").exists())
    self.assertFalse(Member.unscoped.filter(username="other_admin").exists())


class TenantSettingsTests(MemberTestCase):
  def setUp(self):
    _skip_if_off(self)
    super().setUp()
    self.family = Tenant.objects.create(name="Fam", slug="fam")
    self.admin = _make_admin(self.family, "fam_admin")
    set_current_tenant(None)

  def _login_superuser(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)

  def tearDown(self):
    set_current_tenant(None)

  def _base_data(self):
    return {
      "site_name": "",
      "site_logo": "",
      "site_copyright": "",
      "site_footer": "",
      "pdf_size": "A4",
      "dark_mode": False,
      "language_code": "en",
      "time_zone": "Europe/Paris",
      "birthday_days": 50,
      "allow_members_to_create_members": False,
      "allow_members_to_invite_members": False,
      "family_chart_root_person_id": "",
    }

  def test_admin_edits_own_settings_deltas_only(self):
    self.client.force_login(self.admin)
    data = self._base_data()
    data["site_name"] = "Ma Famille"
    resp = self.client.post(reverse("tenants:settings"), data, follow=True)
    self.assertEqual(resp.status_code, 200)
    row = TenantSettings.objects.get(tenant=self.family)
    # only the delta is stored
    self.assertEqual(row.overrides.get("site_name"), "Ma Famille")
    self.assertNotIn("birthday_days", row.overrides)
    self.assertNotIn("pdf_size", row.overrides)

  def test_tenant_setting_reads_override_then_global(self):
    from django.conf import settings as dj_settings
    from tenants.settings_overrides import tenant_setting

    TenantSettings.objects.create(tenant=self.family, overrides={"birthday_days": 7})
    with tenant_context(self.family):
      self.assertEqual(tenant_setting("birthday_days"), 7)
    set_current_tenant(None)
    from tenants.settings_overrides import clear_tenant_settings_cache

    clear_tenant_settings_cache()
    self.assertEqual(tenant_setting("birthday_days"), dj_settings.BIRTHDAY_DAYS)

  def test_chart_root_must_belong_to_tenant(self):
    self.client.force_login(self.admin)
    data = self._base_data()
    data["family_chart_root_person_id"] = self.member.pk  # default tenant member
    resp = self.client.post(reverse("tenants:settings"), data, follow=True)
    self.assertContains(resp, "does not belong to your family")

  def test_non_admin_member_refused(self):
    self.client.login(username=self.member.username, password=self.member.password)  # regular member
    resp = self.client.get(reverse("tenants:settings"))
    self.assertEqual(resp.status_code, 403)

  def test_superuser_can_target_any_tenant(self):
    self._login_superuser()
    resp = self.client.get(reverse("tenants:settings") + "?tenant=fam")
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "Fam")


class AdminEmailRoutingTests(MemberTestCase):
  """Mails to "the admin" go to the requester's family admin (2 families)."""

  def setUp(self):
    _skip_if_off(self)
    super().setUp()
    self.family_b = Tenant.objects.create(name="Bee", slug="bee")
    self.admin_b = _make_admin(self.family_b, "bee_admin")
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_contact_email_goes_to_own_tenant_admin(self):
    from django.core import mail

    self.client.force_login(self.admin_b)
    resp = self.client.post(reverse("core:contact"), {"message": "hello there"}, follow=True)
    self.assertEqual(resp.status_code, 200)
    recipients = [str(e.to) for e in mail.outbox]
    self.assertTrue(any("bee_admin@example.com" in r for r in recipients), recipients)
