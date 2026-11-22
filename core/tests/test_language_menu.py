from django.test import override_settings

from core.templatetags.cm_tags import flag
from members.tests.tests_member_base import MemberTestCase


class LanguageMenuTest(MemberTestCase):
  def test_flag_from_language_code(self):
    self.assertEqual(flag("fr"), "🇫🇷")
    self.assertEqual(flag("en"), "🇬🇧")  # not a country code: mapped explicitly
    self.assertEqual(flag("pt-BR"), "🇵🇹")
    self.assertEqual(flag("bad"), "")

  def test_language_menu_is_in_the_navbar(self):
    response = self.client.get("/")
    self.assertContains(response, 'name="language"')
    self.assertContains(response, "🇫🇷")
    self.assertContains(response, "🇬🇧")

  @override_settings(FEATURES_FLAGS={"show_change_language": False})
  def test_language_menu_hidden_when_feature_disabled(self):
    response = self.client.get("/")
    self.assertNotContains(response, 'name="language"')
