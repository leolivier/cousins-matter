from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from members.tests.tests_member_base import MemberTestCase


class TestAbout(MemberTestCase):
  def test_about(self):
    "Tests the about page displays correctly with all categories."
    response = self.client.get(reverse("cm_main:about"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "cm_main/about/site-stats.html")
    for cat in ["Site", "Members", "Galleries", "Forums", "Chats", "Administrator"]:
      category = slugify(_(cat))
      html = f'<div class="panel-category" id="category-{category}">'
      self.assertContains(response, html)
