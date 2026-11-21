"""i18n tests: the saas catalogues must be loaded and translated."""

from django.test import TestCase
from django.utils import translation


class I18nTests(TestCase):
  def test_catalogues_are_translated(self):
    expected = {
      "fr": ("Nom de la famille", "Créer mon site familial"),
      "es": ("Nombre de la familia", "Crear mi sitio familiar"),
      "de": ("Name der Familie", "Meine Familienseite erstellen"),
      "it": ("Nome della famiglia", "Crea il mio sito familiare"),
      "pt": ("Nome da família", "Criar o meu site familiar"),
    }
    for lang, (family_name, create) in expected.items():
      with translation.override(lang):
        self.assertEqual(translation.gettext("Family name"), family_name, lang)
        self.assertEqual(translation.gettext("Create my family site"), create, lang)

  def test_placeholders_are_interpolated(self):
    with translation.override("fr"):
      self.assertEqual(
        translation.gettext("This link is valid for %(max_age_hours)s hours."),
        "Ce lien est valable %(max_age_hours)s heures.",
      )
