from .base import ChatUITestBase


class PrivateChatRoomsUITest(ChatUITestBase):
  def test_private_chat_rooms_requires_auth(self):
    """The private chat rooms page should redirect to login when not authenticated."""
    self.goto_page("chat:private_chat_rooms")
    self.assert_url_contains("/login/")

  def test_private_chat_rooms_list_display(self):
    """The private chat rooms list should display the private rooms for authenticated users."""
    self.login_and_goto_page("chat:private_chat_rooms")

    self.assert_visible(".panel-heading", "Panel heading should be visible")

    # Our Private Test Room should be visible
    self.page.wait_for_selector(".panel-block")
    self.assertGreaterEqual(self.page.locator(".panel-block").count(), 1)
    self.assert_visible("text=Private Test Room")
    # Should not display the public rooms
    self.assert_hidden("text=Public Test Room")
    self.assert_hidden("text=Empty Room")

  def test_navigate_to_private_room(self):
    """Clicking a room link should navigate to its detail page."""
    self.login_and_goto_page("chat:private_chat_rooms")
    self.page.wait_for_selector(".panel-block a.title")

    # Click Private Test Room link
    room_link = self.page.locator("a.title:has-text('Private Test Room')").first
    room_link.click()

    self.page.wait_for_url(f"**/private/room/{self.private_room.slug}")
    self.assert_visible(".panel-heading")
    self.errors.clear()

  def test_create_private_room(self):
    """Users should be able to create a new private chat room."""
    self.login_and_goto_page("chat:private_chat_rooms")

    self.page.fill("input[name='name']", "A brand new private room")
    self.page.click("button[type='submit']")

    self.page.wait_for_url("**/private/room/a-brand-new-private-room")
    self.assert_visible("text=A brand new private room")

  def test_private_chat_rooms_no_js_errors(self):
    """The private chat rooms list should not produce JavaScript errors."""
    self.login_and_goto_page("chat:private_chat_rooms")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")
