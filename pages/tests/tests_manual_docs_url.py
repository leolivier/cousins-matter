"""The docs link in page_form.html must point at the user manual's Pages/CMS
section *in the current language*: the anchor is mkdocs' slugification of the
translated heading in user-manual/docs/<lang>/features.md."""

from django.urls import reverse
from django.utils.translation import override as lang_override

from core.context_processors import override_settings
from core.templatetags.cm_tags import user_manual_url
from members.tests.tests_member_base import MemberTestCase
from .test_base import BasePageTestCase

# keep in sync with the #heading of "Pages / CMS" per language in user-manual/docs/<lang>/features.md
MANUAL_ANCHORS = {
  "en": "pages-cms",
  "fr": "pages-cms",
  "es": "paginas-cms",
  "pt": "paginas-cms",
  "de": "seiten-cms",
  "it": "pagine-cms",
}


class TestManualDocsUrl(BasePageTestCase, MemberTestCase):
  def test_tag_builds_url_for_current_language(self):
    for lang, anchor in MANUAL_ANCHORS.items():
      with lang_override(lang):
        self.assertEqual(user_manual_url(), f"https://cousins-matter.readthedocs.io/{lang}/latest/features/#{anchor}")

  def test_create_page_links_to_translated_manual(self):
    self.client.login(username=self.superuser.email, password=self.superuser.password)
    for lang, anchor in MANUAL_ANCHORS.items():
      with lang_override(lang), override_settings(LANGUAGE_CODE=lang):
        response = self.client.get(reverse("pages-edit:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"https://cousins-matter.readthedocs.io/{lang}/latest/features/#{anchor}")
