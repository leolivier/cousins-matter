import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


from chat.models import PrivateChatRoom
from members.tests.factories import MemberFactory

from .base import ChatUITestBase


class PrivateRoomDetailUITest(ChatUITestBase):
  """Tests for the private chat room detail page and member/admin management."""

  def setUp(self):
    super().setUp()
    # Create an extra member for leave/remove tests
    self.other_member = MemberFactory(
      username="othermember",
      first_name="Other",
      last_name="Member",
      birthdate="1990-01-01",
    )
    # Add the other member to private_room so we can test leave (need >1 member)
    self.private_room.followers.add(self.other_member)

    # Create a private room with 2 admins for leave-admin tests
    self.multi_admin_room = PrivateChatRoom.objects.create(name="Multi Admin Room")
    self.multi_admin_room.followers.add(self.user)
    self.multi_admin_room.followers.add(self.other_member)
    self.multi_admin_room.admins.add(self.user)
    self.multi_admin_room.admins.add(self.other_member)

  def test_private_room_requires_auth(self):
    """The private room detail page should redirect to login when not authenticated."""
    self.goto_page("chat:private_room", args=[self.private_room.slug])
    self.assert_url_contains("/login/")

  def test_private_room_display(self):
    """The private room detail should display the room name and chat form."""
    self.login_and_goto_page("chat:private_room", args=[self.private_room.slug])

    # Title
    self.assert_visible("h1.title", "Page title should be visible")

    # Room name in panel heading
    self.assert_visible(".panel-heading", "Panel heading should be visible")
    self.assert_visible(f"text={self.private_room.name}", "Room name should be visible")

    # Chat input form
    self.assert_visible("#chat-message-input", "Message input should be visible")
    self.assert_visible("#chat-message-submit", "Submit button should be visible")

    # The leave / members / admins buttons are shown since room_owner is None
    # (no messages) and request.user is authenticated
    self.page.wait_for_timeout(500)

    # Leave button
    leave_btn = self.page.locator("button[hx-post$='/leave/']")
    self.assertTrue(leave_btn.count() > 0, "Leave button should be present")

    # Members and Admins links
    members_link = self.page.locator("a[href$='/members/']")
    self.assertTrue(members_link.count() > 0, "Members link should be present")

    admins_link = self.page.locator("a[href$='/admins/']")
    self.assertTrue(admins_link.count() > 0, "Admins link should be present")
    self.errors.clear()

  def test_private_room_members_list(self):
    """The members list page should display all members of the private room."""
    self.login_and_goto_page("chat:private_room_members", args=[self.private_room.slug])

    self.assert_visible("h1.title", "Page title should be visible")

    # Both admin and other_member should be displayed
    self.assert_visible("text=Admin User", "Admin user should be in members list")
    self.assert_visible("text=Other Member", "Other member should be in members list")

    # Back to room link
    self.assert_visible("a[href*='private/room/']", "Back to room link should be visible")
    self.errors.clear()

  def test_private_room_admins_list(self):
    """The admins list page should display all admins of the private room."""
    self.login_and_goto_page("chat:private_room_admins", args=[self.private_room.slug])

    self.assert_visible("h1.title", "Page title should be visible")

    # Admin user should be in admins list
    self.assert_visible("text=Admin User", "Admin user should be in admins list")

    # Back to room link
    self.assert_visible("a[href*='private/room/']", "Back to room link should be visible")
    self.errors.clear()

  def test_leave_private_room(self):
    """A member should be able to leave a private room."""
    self.login_and_goto_page("chat:private_room", args=[self.multi_admin_room.slug])
    self.page.wait_for_timeout(500)

    # Find the leave button (URL ends with /leave/)
    leave_button = self.page.locator("button[hx-post$='/leave/']")
    self.assertTrue(leave_button.count() > 0, "Leave button should be present")
    self.assertTrue(leave_button.is_visible(), "Leave button should be visible")

    # Handle the hx-confirm dialog
    self.page.on("dialog", lambda dialog: dialog.accept())

    leave_button.click()
    self.page.wait_for_timeout(1500)

    # Should be redirected to private chat rooms list
    self.assertIn("/chat/private", self.page.url)
    self.errors.clear()

  def test_leave_private_room_admins(self):
    """An admin should be able to leave their admin role."""
    self.login_and_goto_page("chat:private_room_admins", args=[self.multi_admin_room.slug])
    self.page.wait_for_timeout(500)

    # Find the leave admins button (URL ends with /admin_leave/)
    leave_admin_button = self.page.locator("button[hx-post$='/admin_leave/']")
    self.assertTrue(leave_admin_button.count() > 0, "Leave admins button should be present")
    self.assertTrue(leave_admin_button.is_visible(), "Leave admins button should be visible")

    # Handle the hx-confirm dialog
    self.page.on("dialog", lambda dialog: dialog.accept())

    leave_admin_button.click()
    self.page.wait_for_timeout(1500)

    # Should be redirected to private chat rooms list
    self.assertIn("/chat/private", self.page.url)
    self.errors.clear()

  def test_remove_member_from_private_room(self):
    """An admin should be able to remove a member from the private room."""
    self.login_and_goto_page("chat:private_room_members", args=[self.private_room.slug])
    self.page.wait_for_timeout(500)

    # Find the remove member button for other_member
    remove_button = self.page.locator(f"button[hx-post*='remove_member/{self.other_member.username}']")
    self.assertTrue(remove_button.count() > 0, "Remove member button should be present")
    self.assertTrue(remove_button.is_visible(), "Remove member button should be visible")

    # Handle the hx-confirm dialog
    self.page.on("dialog", lambda dialog: dialog.accept())

    remove_button.click()
    self.page.wait_for_timeout(1500)

    # Reload the page to get fresh state
    self.goto_page("chat:private_room_members", args=[self.private_room.slug])
    self.page.wait_for_timeout(500)

    # Other member should no longer be listed
    self.assertEqual(
      self.page.locator("text=Other Member").count(),
      0,
      "Removed member should no longer be visible",
    )
    self.errors.clear()

  def test_remove_admin_from_private_room(self):
    """An admin should be able to remove another admin from the private room."""
    self.login_and_goto_page("chat:private_room_admins", args=[self.multi_admin_room.slug])
    self.page.wait_for_timeout(500)

    # Find the remove admin button for other_member
    remove_admin_button = self.page.locator(f"button[hx-post*='remove_admin/{self.other_member.username}']")
    self.assertTrue(remove_admin_button.count() > 0, "Remove admin button should be present")
    self.assertTrue(remove_admin_button.is_visible(), "Remove admin button should be visible")

    # Handle the hx-confirm dialog
    self.page.on("dialog", lambda dialog: dialog.accept())

    remove_admin_button.click()
    self.page.wait_for_timeout(1500)

    # Reload the page to get fresh state
    self.goto_page("chat:private_room_admins", args=[self.multi_admin_room.slug])
    self.page.wait_for_timeout(500)

    # Other member should no longer be in admins list
    self.assertEqual(
      self.page.locator("text=Other Member").count(),
      0,
      "Removed admin should no longer be visible",
    )
    self.errors.clear()

  def test_private_room_no_js_errors(self):
    """The private room detail should not produce JavaScript errors."""
    self.login_and_goto_page("chat:private_room", args=[self.private_room.slug])
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")
