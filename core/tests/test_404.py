from django.contrib.staticfiles import finders
from django.test import TestCase, override_settings


class Custom404PageTest(TestCase):
  """With DEBUG off, Django's default handler renders our 404.html template."""

  def test_unknown_url_uses_custom_404_template(self):
    response = self.client.get("/no/such/path/")
    self.assertEqual(response.status_code, 404)
    self.assertTemplateUsed(response, "404.html")
    self.assertContains(response, "Page not found", status_code=404)
    self.assertContains(response, "core/images/404.svg", status_code=404)
    self.assertIsNotNone(finders.find("core/images/404.svg"))

  @override_settings(DEBUG=True)
  def test_debug_keeps_djangos_technical_404_page(self):
    response = self.client.get("/no/such/path/")
    self.assertEqual(response.status_code, 404)
    self.assertContains(response, "Using the URLconf defined in", status_code=404)
    self.assertTemplateNotUsed(response, "404.html")
