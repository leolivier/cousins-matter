from .base import ChatUITestBase


class PublicChatRoomsUITest(ChatUITestBase):
  def test_public_chat_rooms_requires_auth(self):
    """The chat rooms page should redirect to login when not authenticated."""
    self.goto_page("chat:chat_rooms")
    self.assert_url_contains("/login/")

  def test_public_chat_rooms_list_display(self):
    """The chat rooms list should display the public rooms for authenticated users."""
    self.login_and_goto_page("chat:chat_rooms")

    self.assert_visible(".panel-heading", "Panel heading should be visible")

    # Our Public Test Room should be visible
    self.page.wait_for_selector(".panel-block")
    self.assertGreaterEqual(self.page.locator(".panel-block").count(), 1)
    self.assert_visible("text=Public Test Room")
    self.assert_visible("text=Empty Room")
    # Should not display the private room
    self.assert_hidden("text=Private Test Room")

  def test_navigate_to_public_room(self):
    """Clicking a room link should navigate to its detail page."""
    self.login_and_goto_page("chat:chat_rooms")
    self.page.wait_for_selector(".panel-block a.title")

    # Click Public Test Room link
    room_link = self.page.locator("a.title:has-text('Public Test Room')").first
    room_link.click()

    self.page.wait_for_url(f"**/room/{self.public_room.slug}")
    self.assert_visible(".panel-heading")
    self.errors.clear()

  def test_create_public_room(self):
    """Users should be able to create a new public chat room."""
    self.login_and_goto_page("chat:chat_rooms")

    self.page.fill("input[name='name']", "A brand new room")
    self.page.click("button[type='submit']")

    self.page.wait_for_url("**/room/a-brand-new-room")
    self.assert_visible("text=A brand new room")

  def test_public_chat_rooms_no_js_errors(self):
    """The chat rooms list should not produce JavaScript errors."""
    self.login_and_goto_page("chat:chat_rooms")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")
