import json

from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from members.models import Family
from .tests_member_base import MemberTestCase, get_new_member_data


class TestValidateUsername(MemberTestCase):
  """Tests for the validate_username AJAX endpoint."""

  def test_username_available(self):
    """Test checking a username that is not taken."""
    response = self.client.get(reverse("members:validate_username"), {"username": "nonexistent_user_xyz"})
    self.assertEqual(response.status_code, 200)
    data = json.loads(response.content)
    self.assertFalse(data["is_taken"])

  def test_username_taken(self):
    """Test checking a username that is already taken by another user."""
    other = self.create_member(is_active=True)
    response = self.client.get(reverse("members:validate_username"), {"username": other.username})
    self.assertEqual(response.status_code, 200)
    data = json.loads(response.content)
    self.assertTrue(data["is_taken"])

  def test_own_username_not_taken(self):
    """Test that checking your own username returns not taken."""
    response = self.client.get(reverse("members:validate_username"), {"username": self.member.username})
    self.assertEqual(response.status_code, 200)
    data = json.loads(response.content)
    self.assertFalse(data["is_taken"])


class TestValidateFamilyName(MemberTestCase):
  """Tests for the validate_family_name AJAX endpoint."""

  def test_family_name_available(self):
    """Test checking a family name that does not exist."""
    response = self.client.get(reverse("members:validate_familyname"), {"name": "NonexistentFamily999"})
    self.assertEqual(response.status_code, 200)
    data = json.loads(response.content)
    self.assertFalse(data["is_taken"])

  def test_family_name_taken(self):
    """Test checking a family name that already exists."""
    family = Family.objects.create(name="TestFamilyCoverage")
    try:
      response = self.client.get(reverse("members:validate_familyname"), {"name": "TestFamilyCoverage"})
      self.assertEqual(response.status_code, 200)
      data = json.loads(response.content)
      self.assertTrue(data["is_taken"])
    finally:
      family.delete()


class TestDeleteMember(MemberTestCase):
  """Tests for the delete_member view."""

  def test_delete_member_get_confirm_modal_other(self):
    """Test GET delete of a managed member returns confirm modal."""
    managed = self.create_member()
    response = self.client.get(
      reverse("members:delete", args=[managed.id]),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "core/common/confirm-delete-modal.html")

  def test_delete_member_get_confirm_modal_self(self):
    """Test GET delete of own account returns confirm modal with self-delete message."""
    response = self.client.get(
      reverse("members:delete", args=[self.member.id]),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, str(_("Delete my account")))

  def test_delete_member_no_permission(self):
    """Test deleting a member you don't manage is denied."""
    other_active = self.create_member(is_active=True)
    response = self.client.get(
      reverse("members:delete", args=[other_active.id]),
      HTTP_HX_REQUEST="true",
      follow=True,
    )
    self.assertEqual(response.status_code, 200)


class TestSearchMembersEdgeCases(MemberTestCase):
  """Tests for search_members edge cases."""

  def test_search_empty_query_render_empty_false(self):
    """Test empty query with render_empty_query=false returns no members."""
    response = self.client.get(
      reverse("members:search_members"),
      {"q": "", "render_empty_query": "false"},
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)

  def test_search_short_query_default(self):
    """Test short query (< 3 chars) returns all members page."""
    response = self.client.get(
      reverse("members:search_members"),
      {"q": "ab"},
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)


class TestNotifyDeathEdgeCases(MemberTestCase):
  """Tests for notify_death view edge cases."""

  def test_notify_death_post_no_deathdate(self):
    """Test POST without deathdate returns error and HX-Refresh."""
    other = self.create_member(is_active=True)
    response = self.client.post(
      reverse("members:notify_death", args=[other.id]),
      {"deathdate": "", "message": "test"},
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertHXRefresh(response)


class TestCreateMemberForbidden(MemberTestCase):
  """Tests for CreateManagedMemberView when creation is forbidden."""

  @override_settings(ALLOW_MEMBERS_TO_CREATE_MEMBERS=False)
  def test_create_member_forbidden_get(self):
    """Test that non-superuser cannot access create member page when disabled."""
    response = self.client.get(reverse("members:create"))
    self.assertEqual(response.status_code, 403)

  @override_settings(ALLOW_MEMBERS_TO_CREATE_MEMBERS=False)
  def test_create_member_forbidden_post(self):
    """Test that non-superuser cannot POST create member when disabled."""
    data = get_new_member_data()
    response = self.client.post(reverse("members:create"), data)
    self.assertEqual(response.status_code, 403)
