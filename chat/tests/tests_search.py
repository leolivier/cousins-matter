from django.urls import reverse
from members.tests.tests_member_base import MemberTestCase
from ..models import PrivateChatRoom
from django.template.defaultfilters import slugify


class ChatSearchTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.room_name = "test room"
    self.slug = slugify(self.room_name)
    self.room = PrivateChatRoom.objects.create(name=self.room_name, slug=self.slug)
    self.room.admins.add(self.member)
    self.room.followers.add(self.member)

    # Create another member to search for
    self.other_member = self.create_member(is_active=True)
    self.room.followers.add(self.other_member)

  def tearDown(self):
    self.room.delete()
    super().tearDown()

  def test_search_private_members_htmx(self):
    """Test that HTMX request returns HTML"""
    url = reverse("chat:search_private_members", args=[self.slug])
    # django-htmx middleware checks for HTTP_HX_REQUEST header
    response = self.client.get(url, {"q": self.other_member.first_name}, HTTP_HX_REQUEST="true")
    self.assertEqual(response.status_code, 200)
    self.assertIn("text/html", response["Content-Type"])
    self.assertTemplateUsed(response, "member_search_results")
    self.assertContains(response, self.other_member.full_name)
    self.assertContains(response, "dropdown-item")
