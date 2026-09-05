"""Feature-flag tests: MULTI_TENANT_ENABLED off must hide the whole surface."""

from django.urls import NoReverseMatch, reverse

from members.tests.tests_member_base import MemberTestCase


class MultiTenantOffTests(MemberTestCase):
  """With the flag off, /tenants/ must 404 and the login page shows no link.

  NOTE: the URLconf is built at import time, so we cannot flip
  MULTI_TENANT_ENABLED at runtime here — the flag-off case is the default of
  the test settings; the flag-on suites (tests_family_signup, tests_manage,
  tests_settings) run under MULTI_TENANT_ENABLED=True via the environment.
  """

  def test_tenants_urls_not_resolvable(self):
    from django.conf import settings

    if settings.MULTI_TENANT_ENABLED:
      self.skipTest("flag is on in this environment")
    for name in ("tenants:list", "tenants:create", "tenants:family_signup", "tenants:settings"):
      with self.assertRaises(NoReverseMatch):
        reverse(name)

  def test_tenants_pages_404(self):
    from django.conf import settings

    if settings.MULTI_TENANT_ENABLED:
      self.skipTest("flag is on in this environment")
    self.client.force_login(self.superuser)
    for url in ("/tenants/", "/tenants/create/", "/tenants/signup/", "/tenants/settings/"):
      resp = self.client.get(url)
      self.assertEqual(resp.status_code, 404, url)

  def test_login_page_has_no_family_link_when_off(self):
    from django.conf import settings

    if settings.MULTI_TENANT_ENABLED:
      self.skipTest("flag is on in this environment")
    resp = self.client.get(reverse("members:login"))
    self.assertEqual(resp.status_code, 200)
    self.assertNotContains(resp, "Create a new family")
