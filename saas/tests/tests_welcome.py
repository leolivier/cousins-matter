"""Welcome screen tests: SetPasswordForm + relogin."""

from django.test import RequestFactory, TestCase
from django.urls import reverse

from members.models import Member

from ..models import TenantRequest
from ..tokens import TenantRequestTokenManager
from .utils import skip_if_saas_off

_PWD = "pw-12345-Aa"


class WelcomeTests(TestCase):
  def setUp(self):
    skip_if_saas_off(self)
    # run the whole flow once: request -> link -> validated -> auto-login
    tr = TenantRequest.create_pending(email="founder@example.com", tenant_name="Smith")
    request = RequestFactory().get("/")
    path = TenantRequestTokenManager().generate_link(request, tr).replace("http://testserver", "")
    self.client.get(path)

  def test_welcome_shows_and_sets_password(self):
    resp = self.client.get(reverse("saas:welcome"))
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, "password")

    resp = self.client.post(
      reverse("saas:welcome"),
      {"new_password1": _PWD, "new_password2": _PWD},
    )
    self.assertRedirects(resp, reverse("core:Home"), fetch_redirect_response=False)

    # the session survives the password change and relogin works
    member = Member.unscoped.get(email="founder@example.com")
    self.assertTrue(member.check_password(_PWD))
    self.client.logout()
    self.assertTrue(self.client.login(username="founder@example.com", password=_PWD))

  def test_welcome_redirects_when_password_already_set(self):
    member = Member.unscoped.get(email="founder@example.com")
    member.set_password(_PWD)
    member.save()
    self.client.force_login(member)
    resp = self.client.get(reverse("saas:welcome"))
    self.assertRedirects(resp, reverse("core:Home"), fetch_redirect_response=False)
