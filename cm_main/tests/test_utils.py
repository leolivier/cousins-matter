from django.test import TestCase
from django.utils import translation
from cm_main.utils import translate_date_format


class TestUtils(TestCase):
  def test_translate_date_format(self):
    """Tests that translate_date_format returns expected localized strings."""
    test_cases = [
      ("fr", "%d/%m/%Y", "JJ/MM/AAAA"),
      ("fr", "%d-%m-%y %H:%M:%S", "JJ-MM-AA HH:mm:ss"),
      ("en", "%d/%m/%Y", "DD/MM/YYYY"),
      ("en", "%I:%M %p", "hh:mm AM/PM"),
      ("es", "%d/%m/%Y", "DD/MM/AAAA"),
      ("it", "%d/%m/%Y", "GG/MM/AAAA"),
      ("it", "%H:%M", "OO:mm"),
      ("pt", "%d/%m/%Y", "DD/MM/AAAA"),
      ("de", "%d.%m.%Y", "TT.MM.JJJJ"),
    ]

    for lang, fmt, expected in test_cases:
      with self.subTest(lang=lang, fmt=fmt):
        with translation.override(lang):
          result = translate_date_format(fmt)
          self.assertEqual(
            result,
            expected,
            f"Failed for language '{lang}' with format '{fmt}'",
          )
