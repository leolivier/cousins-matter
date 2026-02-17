from unittest.mock import patch
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from django.utils.translation import gettext as _
from members.tests.tests_member_base import MemberTestCase


class GedcomViewsTest(MemberTestCase):
  def test_import_gedcom_get(self):
    response = self.client.get(reverse("genealogy:import_gedcom"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/import_gedcom.html")
    self.assertIn("form", response.context)

  @patch("genealogy.views.views_gedcom.GedcomParser")
  @patch("genealogy.views.views_gedcom.clear_genealogy_caches")
  def test_import_gedcom_post_success(self, mock_clear_caches, mock_parser_class):
    mock_parser = mock_parser_class.return_value
    gedcom_content = b"0 HEAD\n1 CHAR UTF-8\n0 TRLR"
    gedcom_file = SimpleUploadedFile("test.ged", gedcom_content)

    response = self.client.post(reverse("genealogy:import_gedcom"), {"gedcom_file": gedcom_file})

    self.assertRedirects(response, reverse("genealogy:dashboard"))
    mock_parser.parse.assert_called_once()
    mock_clear_caches.assert_called_once()

    # Check success message
    messages = list(get_messages(response.wsgi_request))
    self.assertEqual(len(messages), 1)
    self.assertEqual(str(messages[0]), _("GEDCOM imported successfully."))

  def test_import_gedcom_post_invalid_form(self):
    response = self.client.post(reverse("genealogy:import_gedcom"), {})
    self.assertEqual(response.status_code, 200)
    # In Django 5.0+, assertFormError doesn't take response as first argument
    from django.utils.translation import gettext as _

    self.assertFormError(response.context["form"], "gedcom_file", _("This field is required."))

  @patch("genealogy.views.views_gedcom.GedcomParser")
  def test_import_gedcom_post_parser_error(self, mock_parser_class):
    mock_parser = mock_parser_class.return_value
    mock_parser.parse.side_effect = Exception("Parsing error")
    gedcom_file = SimpleUploadedFile("test.ged", b"invalid content")

    response = self.client.post(reverse("genealogy:import_gedcom"), {"gedcom_file": gedcom_file})

    self.assertRedirects(response, reverse("genealogy:dashboard"))

    # Check error message
    messages = list(get_messages(response.wsgi_request))
    self.assertEqual(len(messages), 1)
    expected_msg = _("Error importing GEDCOM: %(error)s") % {"error": "Parsing error"}
    self.assertEqual(str(messages[0]), expected_msg)

  @patch("genealogy.views.views_gedcom.GedcomExporter")
  def test_export_gedcom(self, mock_exporter_class):
    mock_exporter = mock_exporter_class.return_value
    mock_exporter.export.return_value = "GEDCOM CONTENT"

    response = self.client.get(reverse("genealogy:export_gedcom"))

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content.decode(), "GEDCOM CONTENT")
    self.assertEqual(response["Content-Type"], "text/gedcom")
    self.assertIn("attachment; filename=", response["Content-Disposition"])

  @patch("genealogy.views.views_gedcom.GedcomExporter")
  def test_download_gedcom(self, mock_exporter_class):
    mock_exporter = mock_exporter_class.return_value
    mock_exporter.export.return_value = "GEDCOM CONTENT"

    response = self.client.get(reverse("genealogy:download_gedcom"))

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.content.decode(), "GEDCOM CONTENT")
    self.assertEqual(response["Content-Type"], "text/plain")
