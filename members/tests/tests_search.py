from django.urls import reverse

from members.models import Member

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
    self.assertContains(response, reverse("members:detail", args=[self.other_member.username]))

  def test_search_by_username(self):
    """#491: searching by username finds member even if username contains neither first nor last name"""
    member = self.create_member(
      {
        "username": "bibi67",
        "first_name": "Robert",
        "last_name": "Dupont",
        "email": "bibi67@example.com",
        "password": "bibi67password!",
      },
      is_active=True,
    )
    self.assertIn(member, Member.objects.fuzzy_search("bibi67"))
    # same through the members screen search (service wrapping fuzzy_search)
    url = reverse("members:search_members")
    response = self.client.get(url, {"q": "bibi67"}, HTTP_HX_REQUEST="true")
    self.assertContains(response, member.full_name)
