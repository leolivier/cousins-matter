from django.urls import reverse
from .tests_member_base import MemberTestCase


class MemberSearchTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    # Create another member to search for
    self.other_member = self.create_member(is_active=True)

  def test_search_members_htmx(self):
    """Test that HTMX request returns HTML"""
    url = reverse("members:search_members")
    # django-htmx middleware checks for HTTP_HX_REQUEST header
    response = self.client.get(url, {"q": self.other_member.first_name}, HTTP_HX_REQUEST="true")
    self.assertEqual(response.status_code, 200)
    # Content-Type for render is usually text/html; charset=utf-8
    self.assertIn("text/html", response["Content-Type"])
    self.assertTemplateUsed(response, "members_content")
    self.assertContains(response, self.other_member.full_name)
    self.assertContains(response, reverse("members:detail", args=[self.other_member.id]))
