"""Automated version of the tenant onboarding E2E scenario.

Mirrors ``docs/flows/tenant-onboarding-e2e.md`` phases 1-7: self-service family
signup, first tenant admin, managed member creation, join request, invitation,
invited-person registration and login on the family site.

The scenario is stateful from phase to phase; each test rebuilds the state it
needs through the private ``_...`` scenario steps, so tests stay independent
while the ``test_NN_`` numbering keeps the report in scenario order.

The ``/tenants/`` URLconf is mounted at import time from
``settings.MULTI_TENANT_ENABLED``, so these tests must run in multi-tenant mode
(they skip otherwise)::

    make test-mt t=tenants.tests.tests_onboarding_e2e

or run ``scripts/tests/run_tenant_onboarding_e2e.sh``.
"""

import re

from captcha.conf import settings as captcha_settings
from django.conf import settings
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from members.models import Member
from tenants.models import Tenant, TenantSettings
from tenants.scoping import set_current_tenant


@override_settings(LANGUAGE_CODE="en")
class TenantOnboardingE2ETests(TestCase):
  """Phases 1-7 of the tenant onboarding scenario, plus the signed-link edge."""

  FAMILY_NAME = "Test Family ETA"
  FAMILY_SLUG = "test-family-eta"
  NORA_EMAIL = "nora@example.com"
  MARTA_EMAIL = "marta@example.com"
  HUGO_EMAIL = "hugo@example.com"
  PWD = "pw-12345-Aa"

  def setUp(self):
    if not settings.MULTI_TENANT_ENABLED:
      self.skipTest("MULTI_TENANT_ENABLED is off: /tenants/ is not mounted")
    # the signup and join forms are IP-throttled through the shared cache,
    # which is not rolled back between tests
    cache.clear()
    mail.outbox.clear()
    # "private window" used by the outsider and then by the invitee
    self.anonymous = Client()
    # the join form captcha is a human-only gate; tests type the test-mode answer
    self._captcha_test_mode = captcha_settings.CAPTCHA_TEST_MODE
    captcha_settings.CAPTCHA_TEST_MODE = True

  def tearDown(self):
    captcha_settings.CAPTCHA_TEST_MODE = self._captcha_test_mode
    set_current_tenant(None)
    cache.clear()
    super().tearDown()

  # -- scenario fixtures ---------------------------------------------------

  def _signup_data(self):
    return {
      "name": self.FAMILY_NAME,
      "username": "nora",
      "email": self.NORA_EMAIL,
      "password1": self.PWD,
      "password2": self.PWD,
      "first_name": "Nora",
      "last_name": "Admin",
      "birthdate": "1990-01-01",
      "privacy_consent": "on",
      "email_batch_frequency": "immediate",
    }

  def _marta_data(self):
    return {
      "username": "marta",
      "email": self.MARTA_EMAIL,
      "first_name": "Marta",
      "last_name": "Managed",
      "birthdate": "1995-05-05",
      "phone": "01 23 45 67 89",
      "email_batch_frequency": "immediate",
    }

  def _join_data(self):
    return {
      "name": "Hugo",
      "email": self.HUGO_EMAIL,
      "message": "Hello, this is Hugo, may I join the family?",
      "captcha_0": "whatever",
      "captcha_1": "passed",
    }

  def _hugo_data(self, email=None):
    return {
      "username": "hugo",
      "email": email or self.HUGO_EMAIL,
      "password1": self.PWD,
      "password2": self.PWD,
      "first_name": "Hugo",
      "last_name": "Invitee",
      "birthdate": "1998-02-02",
      "privacy_consent": "on",
      "email_batch_frequency": "immediate",
    }

  # -- scenario steps (each one rebuilds the state it needs) ---------------

  def _sign_up(self):
    """Phase 1 action: self-service family signup. Returns the response."""
    mail.outbox.clear()
    return self.client.post(reverse("tenants:family_signup"), self._signup_data(), follow=True)

  def _admin_logged_in(self):
    """Phases 1-2: signup, email activation, then login as the family admin."""
    self._sign_up()
    activation_url = self._email_link(mail.outbox[0], "/user/verify-email/")
    response = self.anonymous.get(activation_url, follow=True)
    self.assertEqual(response.status_code, 200)
    nora = Member.unscoped.get(email=self.NORA_EMAIL)
    self.assertTrue(nora.is_active)
    self.assertTrue(self.client.login(username=self.NORA_EMAIL, password=self.PWD))
    return nora.tenant

  def _managed_member_created(self):
    """Phase 3: the admin creates an inactive managed member."""
    tenant = self._admin_logged_in()
    response = self.client.post(reverse("members:create"), self._marta_data(), follow=True)
    self.assertEqual(response.status_code, 200)
    return tenant, response

  def _join_request_sent(self):
    """Phase 4: an anonymous outsider requests to join the family."""
    self._admin_logged_in()
    mail.outbox.clear()
    response = self.anonymous.post(reverse("tenant-join", args=[self.FAMILY_SLUG]), self._join_data())
    self.assertRedirects(response, reverse("tenant-home", args=[self.FAMILY_SLUG]))
    self.assertEqual(len(mail.outbox), 1)
    return mail.outbox[0]

  def _invitation_sent(self):
    """Phase 5: the admin answers the join request with an invitation."""
    self._join_request_sent()
    mail.outbox.clear()
    response = self.client.post(reverse("members:invite"), {"invited": "Hugo", "email": self.HUGO_EMAIL})
    self.assertEqual(response.status_code, 200)
    self.assertEqual(len(mail.outbox), 1)
    return self._email_link(mail.outbox[0], "/members/register/")

  def _register_invitee(self, email=None):
    """Phase 6: the invited person registers through the signed link."""
    invitation_url = self._invitation_sent()
    page = self.anonymous.get(invitation_url)
    self.assertEqual(page.status_code, 200)
    mail.outbox.clear()
    return self.anonymous.post(invitation_url, self._hugo_data(email), follow=True)

  # -- email helpers -------------------------------------------------------

  @staticmethod
  def _html_body(email):
    for content, mimetype in email.alternatives:
      if mimetype == "text/html":
        return content
    return email.body

  def _email_link(self, email, path_fragment):
    links = re.findall(r"https?://testserver[^\s\"'<>]+", self._html_body(email))
    for link in links:
      if path_fragment in link:
        return link
    self.fail(f"no link containing {path_fragment!r} in email; found {links}")

  # -- phases --------------------------------------------------------------

  def test_01_self_signup_creates_family_and_inactive_admin(self):
    response = self._sign_up()
    self.assertEqual(response.redirect_chain[-1][0], reverse("members:login"))
    self.assertContains(
      response,
      _(
        "Your new family space has been created! You will now receive an email to verify your "
        "email address. Click in the link inside the mail to finish the registration."
      ),
    )
    family = Tenant.objects.get(slug=self.FAMILY_SLUG)
    self.assertEqual(family.name, self.FAMILY_NAME)
    self.assertTrue(TenantSettings.objects.filter(tenant=family).exists())
    nora = Member.unscoped.get(email=self.NORA_EMAIL)
    self.assertEqual(nora.tenant_id, family.pk)
    self.assertEqual(nora.role, Member.Role.ADMIN)
    self.assertFalse(nora.is_active)  # pending email verification
    self.assertEqual(len(mail.outbox), 1)
    self.assertSequenceEqual(mail.outbox[0].recipients(), [self.NORA_EMAIL])

  def test_02_first_login_exposes_family_admin_powers_only(self):
    self._admin_logged_in()
    self.assertEqual(self.client.get("/").status_code, 200)
    self.assertEqual(self.client.get(reverse("members:invite")).status_code, 200)
    self.assertEqual(self.client.get(reverse("tenants:settings")).status_code, 200)
    # the family lifecycle is platform-admin business
    self.assertEqual(self.client.get(reverse("tenants:list")).status_code, 403)

  def test_03_admin_creates_an_inactive_managed_member(self):
    family, response = self._managed_member_created()
    self.assertContains(response, _("Member successfully created"))
    self.assertEqual(response.redirect_chain[-1][0], reverse("members:detail", args=["marta"]))
    marta = Member.unscoped.get(username="marta")
    self.assertEqual(marta.tenant_id, family.pk)
    self.assertFalse(marta.is_active)
    self.assertEqual(marta.member_manager.email, self.NORA_EMAIL)
    # an inactive account cannot sign in
    self.assertFalse(self.client.login(username=self.MARTA_EMAIL, password=self.PWD))

  def test_04_join_request_from_outsider_reaches_family_admin(self):
    self._admin_logged_in()
    home = self.anonymous.get(reverse("tenant-home", args=[self.FAMILY_SLUG]))
    self.assertEqual(home.status_code, 200)
    self.assertContains(home, reverse("tenant-join", args=[self.FAMILY_SLUG]))
    join_page = self.anonymous.get(reverse("tenant-join", args=[self.FAMILY_SLUG]))
    self.assertEqual(join_page.status_code, 200)

    mail.outbox.clear()
    response = self.anonymous.post(reverse("tenant-join", args=[self.FAMILY_SLUG]), self._join_data(), follow=True)
    self.assertEqual(response.redirect_chain[-1][0], reverse("tenant-home", args=[self.FAMILY_SLUG]))
    self.assertContains(response, _("Registration request sent."))
    self.assertEqual(len(mail.outbox), 1)
    request_mail = mail.outbox[0]
    self.assertSequenceEqual(request_mail.recipients(), [self.NORA_EMAIL])
    self.assertEqual(request_mail.subject, _("Registration request for %(site_name)s") % {"site_name": settings.SITE_NAME})
    self.assertIn(reverse("members:invite") + f"?mail={self.HUGO_EMAIL}", self._html_body(request_mail))

  def test_05_admin_invitation_is_prefilled_and_sent(self):
    self._join_request_sent()
    page = self.client.get(reverse("members:invite"), {"mail": self.HUGO_EMAIL})
    self.assertEqual(page.status_code, 200)
    self.assertEqual(page.context["form"].initial.get("email"), self.HUGO_EMAIL)

    mail.outbox.clear()
    response = self.client.post(reverse("members:invite"), {"invited": "Hugo", "email": self.HUGO_EMAIL})
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, _("Invitation sent to %(email)s.") % {"email": self.HUGO_EMAIL})
    # the shareable family home URL is displayed
    self.assertContains(response, reverse("tenant-home", args=[self.FAMILY_SLUG]))
    # inviting does not create a member yet
    self.assertFalse(Member.unscoped.filter(email=self.HUGO_EMAIL).exists())
    self.assertEqual(len(mail.outbox), 1)
    self.assertSequenceEqual(mail.outbox[0].recipients(), [self.HUGO_EMAIL])
    self._email_link(mail.outbox[0], "/members/register/")

  def test_06_invitee_registers_prefilled_and_directly_active(self):
    invitation_url = self._invitation_sent()
    page = self.anonymous.get(invitation_url)
    self.assertEqual(page.status_code, 200)
    self.assertEqual(page.context["form"].initial.get("email"), self.HUGO_EMAIL)
    self.assertEqual(page.context["form"].initial.get("first_name"), "Hugo")

    mail.outbox.clear()
    response = self.anonymous.post(invitation_url, self._hugo_data(), follow=True)
    self.assertEqual(response.redirect_chain[-1][0], reverse("members:login"))
    self.assertContains(
      response,
      _("Hello %(username)s, your account is now active! You can now sign in.") % {"username": "hugo"},
    )
    self.assertEqual(len(mail.outbox), 0)  # the signed link already proved the email
    hugo = Member.unscoped.get(email=self.HUGO_EMAIL)
    self.assertTrue(hugo.is_active)
    self.assertEqual(hugo.tenant.slug, self.FAMILY_SLUG)

  def test_07_invited_member_logs_in_on_the_family_site(self):
    self._register_invitee()
    # login is by email (ACCOUNT_LOGIN_METHODS = {"email"})
    response = self.anonymous.post(reverse("members:login"), {"username": self.HUGO_EMAIL, "password": self.PWD}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.wsgi_request.user.is_authenticated)
    self.assertEqual(response.wsgi_request.user.email, self.HUGO_EMAIL)
    self.assertEqual(self.anonymous.get(reverse("members:members")).status_code, 200)
    self.assertEqual(self.anonymous.get(reverse("members:detail", args=["hugo"])).status_code, 200)

  def test_08_tampered_invitation_link_is_rejected(self):
    invitation_url = self._invitation_sent()
    tampered = invitation_url[:-1] + ("0" if invitation_url[-1] != "0" else "1")
    response = self.anonymous.get(tampered, follow=True)
    self.assertContains(response, _("Invalid link. Please contact the administrator."))
    self.assertEqual(response.redirect_chain[-1][0], "/")
    self.assertFalse(Member.unscoped.filter(email=self.HUGO_EMAIL).exists())
