import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


from chat.tests.factories import ChatMessageFactory, ChatRoomFactory
from members.tests.factories import MemberFactory

from .base import ChatUITestBase


class PublicRoomDetailUITest(ChatUITestBase):
  """Tests for the public chat room detail page."""

  def setUp(self):
    super().setUp()
    # Create a room with 30 messages for pagination tests
    self.big_room = ChatRoomFactory(name="Big Paginated Room", create_messages=False)
    members = [MemberFactory() for _ in range(3)]
    for i in range(30):
      ChatMessageFactory(
        room=self.big_room,
        member=members[i % 3],
        content=f"Message number {i}",
      )

  def test_public_room_requires_auth(self):
    """The public room detail page should redirect to login when not authenticated."""
    self.goto_page("chat:room", args=[self.public_room.slug])
    self.assert_url_contains("/login/")

  def test_public_room_display(self):
    """The public room detail should display the room name, messages, and chat form."""
    self.login_and_goto_page("chat:room", args=[self.public_room.slug])

    # Title
    self.assert_visible("h1.title", "Page title should be visible")

    # Room name in panel heading
    self.assert_visible(".panel-heading", "Panel heading should be visible")
    self.assert_visible(f"text={self.public_room.name}", "Room name should be visible")

    # Messages section
    self.assert_visible("#chat-messages", "Chat messages container should be visible")

    # Chat input form
    self.assert_visible("#chat-message-input", "Message input should be visible")
    self.assert_visible("#chat-message-submit", "Submit button should be visible")

    # Edit button (user is superuser, so they can edit)
    self.assert_visible("button[hx-get$='/edit']", "Edit button should be visible")

    # At least one message should be displayed (factory creates 5-15 messages)
    messages = self.page.locator("#chat-messages .panel-block")
    self.assertGreaterEqual(messages.count(), 1, "At least one message should be displayed")
    self.errors.clear()

  def test_public_room_empty_display(self):
    """An empty public room should display the form but no messages."""
    self.login_and_goto_page("chat:room", args=[self.empty_room.slug])

    self.assert_visible("h1.title", "Page title should be visible")
    self.assert_visible("#chat-message-input", "Message input should be visible")
    self.assert_visible("#chat-message-submit", "Submit button should be visible")

    # Messages should be absent or empty
    messages = self.page.locator("#chat-messages .panel-block")
    self.assertEqual(messages.count(), 0, "No messages should be displayed in empty room")
    self.errors.clear()

  def test_public_room_pagination(self):
    """The room with many messages should display pagination links."""
    self.login_and_goto_page("chat:room", args=[self.big_room.slug])

    # Should see pagination links (30 messages, 25 per page = 2 pages)
    self.page.wait_for_selector(".pagination")

    # Navigate to page 2
    page_links = self.page.locator("a.pagination-link")
    if page_links.count() > 1:
      page_links.last.click()
      self.page.wait_for_timeout(500)
      # URL should contain page number
      self.assertIn("/2", self.page.url, "Should navigate to page 2")

    self.errors.clear()

  def test_toggle_follow(self):
    """Clicking the follow/unfollow button should toggle following status."""
    self.login_and_goto_page("chat:room", args=[self.public_room.slug])

    # Find the follow toggle link
    follow_link = self.page.locator("a[href*='toggle-follow']")
    self.assertTrue(follow_link.is_visible(), "Follow toggle link should be visible")

    # Click it
    follow_link.click()
    self.page.wait_for_timeout(500)

    # After toggle, the page should still be accessible
    self.assert_visible(".panel-heading", "Room page should still be visible after toggle")
    self.errors.clear()

  def test_edit_room_name(self):
    """The room name should be editable via HTMX inline form."""
    self.login_and_goto_page("chat:room", args=[self.public_room.slug])

    # Click the edit button
    edit_button = self.page.locator("button[hx-get$='/edit']")
    self.assertTrue(edit_button.is_visible(), "Edit button should be visible")
    edit_button.click()
    self.page.wait_for_timeout(500)

    # The edit form should appear with an input
    name_input = self.page.locator("input[name='room-name']")
    self.assertTrue(name_input.is_visible(), "Room name input should appear")

    # Change the name and submit by pressing Enter
    new_name = "Renamed Public Room"
    name_input.fill(new_name)
    name_input.press("Enter")
    self.page.wait_for_timeout(1000)

    # URL should update with new slug
    self.assertIn("renamed-public-room", self.page.url, "URL should reflect the new room name")
    self.assert_visible(f"text={new_name}", "New room name should be visible")
    self.errors.clear()

  def test_delete_room(self):
    """The room should be deletable via the confirm-delete modal."""
    self.login_and_goto_page("chat:room", args=[self.empty_room.slug])

    # Click the delete button (hx-get to load the modal)
    delete_button = self.page.locator("button[hx-get$='/delete']")
    self.assertTrue(delete_button.is_visible(), "Delete button should be visible")
    delete_button.click()
    # Wait for the modal to appear inside #modal div
    self.page.wait_for_selector("#modal .modal", timeout=3000)

    # The modal should be visible
    self.assert_visible("#modal .modal", "Delete confirmation modal should appear")

    # Fill the confirmation field with the room name
    # Use pressSequentially to trigger keyup events that activate the submit button
    confirmation_input = self.page.locator("#modal input.confirmation_check")
    if confirmation_input.is_visible():
      confirmation_input.click()
      confirmation_input.press_sequentially(self.empty_room.name)
      self.page.wait_for_timeout(300)

    # Click the delete submit button in the modal
    submit_button = self.page.locator("#modal button[type='submit']")
    self.assertTrue(submit_button.is_visible(), "Submit button in modal should be visible")
    self.assertFalse(submit_button.is_disabled(), "Submit button should be enabled after confirmation")
    submit_button.click()
    self.page.wait_for_timeout(1500)

    # Should be redirected to the chat rooms list
    self.assertIn("/chat/", self.page.url)
    # The room slug should not be in the path anymore
    self.assertFalse(
      f"room/{self.empty_room.slug}" in self.page.url,
      "Should not be on the deleted room detail page anymore",
    )
    self.errors.clear()

  def test_public_room_no_js_errors(self):
    """The public room detail should not produce JavaScript errors."""
    self.login_and_goto_page("chat:room", args=[self.public_room.slug])
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")
