"""Landing page takeover tests (run with MULTI_TENANT_ENABLED=True SAAS_LANDING_ENABLED=True)."""

from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from core.views.views_general import HomeView
from members.models import Member

from .utils import skip_if_saas_off


class LandingTests(TestCase):
  def setUp(self):
    skip_if_saas_off(self)

  def test_anonymous_gets_landing(self):
    resp = self.client.get("/")
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, reverse("saas:signup"))
    # spec content: demo + docs links
    self.assertContains(resp, settings.SAAS_DEMO_URL)
    self.assertContains(resp, settings.SAAS_DOCS_URL)

  def test_docs_link_follows_page_language(self):
    """Both doc links point to the readthedocs edition matching the page language."""
    self.client.cookies["django_language"] = "fr"
    resp = self.client.get("/")
    self.assertEqual(resp.status_code, 200)
    self.assertContains(resp, f"{settings.SAAS_DOCS_URL}fr/latest/", count=2)

  def test_authenticated_gets_app_home(self):
    member = Member.objects.create(username="joe", email="joe@example.com", first_name="Joe", last_name="Dalton")
    member.set_password("pw-12345-Aa")
    member.save()
    self.client.force_login(member)
    resp = self.client.get("/")
    self.assertEqual(resp.status_code, 200)
    self.assertNotContains(resp, reverse("saas:signup"))

  def test_flag_off_keeps_normal_home(self):
    """With the flag off the HomeView keeps rendering the regular home."""
    request = RequestFactory().get("/")
    request.user = type("anon", (), {"is_anonymous": True})()
    view = HomeView()
    view.setup(request)
    with override_settings(SAAS_LANDING_ENABLED=False):
      self.assertEqual(view.get_template_names(), ["core/base.html"])
    self.assertEqual(view.get_template_names(), ["saas/landing.html"])
