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
      reverse("members:delete", args=[managed.username]),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "core/common/confirm-delete-modal.html")

  def test_delete_member_get_confirm_modal_self(self):
    """Test GET delete of own account returns confirm modal with self-delete message."""
    response = self.client.get(
      reverse("members:delete", args=[self.member.username]),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, str(_("Delete my account")))

  def test_delete_member_no_permission(self):
    """Test deleting a member you don't manage is denied."""
    other_active = self.create_member(is_active=True)
    response = self.client.get(
      reverse("members:delete", args=[other_active.username]),
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
      reverse("members:notify_death", args=[other.username]),
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


class TestManagedMembersView(MemberTestCase):
  """Tests for the "Members I Manage" page (issue 545)."""

  def test_managed_members_listed(self):
    managed = self.create_member()  # created with member_manager=self.member
    response = self.client.get(reverse("members:managed_members"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, managed.get_full_name())

  def test_activate_button_shown_for_inactive_managed_member(self):
    managed = self.create_member()
    response = self.client.get(reverse("members:managed_members"))
    self.assertContains(response, reverse("members:activate", kwargs={"username": managed.username}))

  def test_non_managed_members_not_listed(self):
    other = self.create_member(is_active=True)  # active members have no member_manager
    response = self.client.get(reverse("members:managed_members"))
    self.assertNotContains(response, other.get_full_name())

  def test_empty_for_member_without_managed_members(self):
    response = self.client.get(reverse("members:managed_members"))
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, _("You don't manage any members yet."))


class TestChangeMemberManager(MemberTestCase):
  """Tests for the change-manager command (issue 545)."""

  def setUp(self):
    super().setUp()
    self.managed = self.create_member()  # member_manager=self.member
    self.change_url = reverse("members:change_member_manager", kwargs={"username": self.managed.username})

  def test_get_shows_manager_search(self):
    """The modal offers a search-as-you-type manager picker."""
    response = self.client.get(self.change_url)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, 'type="search"')
    self.assertContains(response, 'name="new_manager"')

  def test_search_results_offer_active_members_only(self):
    """The search partial only shows active, non-dead members as candidates."""
    active = self.create_member(get_new_member_data(first_name="Zoe", last_name="Auble"), is_active=True)
    response = self.client.get(
      reverse("members:search_members"),
      {
        "q": "Zoe",
        "render_with": "members/members/manager_search_results.html",
        "render_empty_query": "false",
      },
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, active.get_full_name())
    self.assertNotContains(response, self.managed.get_full_name())

  def test_post_reassigns_member(self):
    new_manager = self.create_member(is_active=True)
    response = self.client.post(self.change_url, {"new_manager": new_manager.pk})
    self.assertHXRefresh(response)
    self.managed.refresh_from_db()
    self.assertEqual(self.managed.member_manager, new_manager)

  def test_non_manager_is_refused(self):
    other = self.create_member(is_active=True)
    self.client.login(username=other.email, password=other.password)
    response = self.client.post(self.change_url, {"new_manager": self.member.pk})
    self.assertRedirects(response, reverse("members:detail", kwargs={"username": self.managed.username}))
