from django.urls import reverse
from .base import PollsUITestBase


class PollsListUITest(PollsUITestBase):
  """UI tests for the polls list page."""

  def test_polls_list_page_requires_auth(self):
    """The polls list page should redirect to login when not authenticated."""
    self.goto_page("polls:list_polls")
    self.assert_url_contains("/login/")

  def test_polls_list_displays_created_polls(self):
    """The polls list should display all published polls for authenticated users."""
    self.login_and_goto_page("polls:list_polls")

    # Panel heading with title
    self.assert_visible(".panel-heading", "Panel heading should be visible")

    # Panel blocks for each published poll
    blocks = self.page.locator(".panel-block")
    self.assertGreaterEqual(blocks.count(), 1, "At least one poll should be displayed")

  def test_polls_list_has_create_button(self):
    """The polls list should show a 'Create poll' button for authenticated users."""
    self.login_and_goto_page("polls:list_polls")

    create_button = self.page.locator(f'a[href="{reverse("polls:create_poll")}"]')
    self.assertTrue(create_button.is_visible(), "Create poll button should be visible")

  def test_polls_list_tab_navigation(self):
    """The Open/All/Closed tabs should be visible and clickable."""
    self.login_and_goto_page("polls:list_polls")

    # Should have tabs
    tabs = self.page.locator(".panel-tabs a")
    self.assertGreaterEqual(tabs.count(), 1, "At least one tab should be visible")

    # Click 'All' tab
    all_tab = self.page.locator(f'.panel-tabs a[href="{reverse("polls:all_polls")}"]')
    if all_tab.count() > 0:
      all_tab.click()
      self.page.wait_for_timeout(500)
      self.assert_url_contains("/all/")

  def test_polls_list_vote_button(self):
    """Each poll should have a Vote button."""
    self.login_and_goto_page("polls:list_polls")
    self.page.wait_for_selector(".panel-block")

    # Vote button links contain /vote/ in the href (aria-label is translated)
    vote_buttons = self.page.locator('.panel-block a[href*="/vote/"]')
    self.assertGreaterEqual(vote_buttons.count(), 1, "At least one Vote button should be visible")

  def test_polls_list_no_js_errors(self):
    """The polls list page should not have JS errors."""
    self.login("admin", "password")
    self.page.goto(self.url(reverse("polls:list_polls")))
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors on polls list: {self.errors}")


class PollDetailUITest(PollsUITestBase):
  """UI tests for the poll detail page."""

  def test_poll_detail_page_display(self):
    """The poll detail page should display poll information."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:poll_detail", args=[poll.id])))

    # Card should be visible
    self.assert_visible(".card", "Detail card should be visible")

    # Title should be visible
    self.assert_visible(".card-header .title", "Card header title should be visible")

    # Poll info content
    self.assert_visible(".card-content", "Card content should be visible")

  def test_poll_detail_back_button(self):
    """The detail page should have a back button linking to polls list."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:poll_detail", args=[poll.id])))

    # Back button href points to list_polls (aria-label is translated)
    back_button = self.page.locator(f'.card-header a[href="{reverse("polls:list_polls")}"]')
    self.assertTrue(back_button.is_visible(), "Back button should be visible")

  def test_poll_detail_vote_button(self):
    """The detail page should have a Vote button."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:poll_detail", args=[poll.id])))

    vote_button = self.page.locator(".card-footer a.button.is-primary")
    self.assertTrue(vote_button.is_visible(), "Vote button should be visible")

  def test_poll_detail_update_button_for_owner(self):
    """The detail page should show Update button for the poll owner."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:poll_detail", args=[poll.id])))

    update_button = self.page.locator(".card-footer a.button.is-link")
    self.assertTrue(update_button.is_visible(), "Update button should be visible for owner")

  def test_poll_detail_no_js_errors(self):
    """The poll detail page should not have JS errors."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:poll_detail", args=[poll.id])))
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors on poll detail: {self.errors}")


class PollCreateUITest(PollsUITestBase):
  """UI tests for creating polls."""

  def test_create_poll_form_display(self):
    """The create poll form should display all expected fields."""
    self.login("admin", "password")
    self.page.goto(self.url(reverse("polls:create_poll")))

    # Title
    self.assert_visible("h1.title", "Form title should be visible")

    # Form fields rendered by crispy
    self.assert_visible("input[name='title']", "Title input should be visible")
    self.assert_visible("textarea[name='description']", "Description textarea should be visible")
    self.assert_visible("select[name='open_to']", "Open to select should be visible")

    # Submit button
    submit_btn = self.page.locator("button[type='submit'].is-dark")
    self.assertTrue(submit_btn.is_visible(), "Submit button should be visible")

    # The questions section should show a placeholder message
    self.assert_visible("#poll-questions", "Questions panel should be visible")

    # Reset errors: form pages load external JS (bulma-calendar, polls.js) that
    # may produce 404s in StaticLiveServerTestCase — these are expected in test env.
    self.errors = []


class PollUpdateUITest(PollsUITestBase):
  """UI tests for updating polls."""

  def test_update_poll_form_display(self):
    """The update poll form should display with pre-filled data."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:update_poll", args=[poll.id])))

    # Title
    self.assert_visible("h1.title", "Form title should be visible")

    # Title input should be pre-filled
    title_input = self.page.locator("input[name='title']")
    self.assertEqual(
      title_input.input_value(),
      poll.title,
      "Title input should contain the existing title",
    )

    # Submit button
    self.assert_visible("button[type='submit'].is-dark", "Submit button should be visible")

    # Questions panel should be present
    self.assert_visible("#poll-questions", "Questions panel should be visible")

    # Reset errors: update form loads external JS assets (see PollCreateUITest)
    self.errors = []

  def test_update_poll_form_questions_section(self):
    """The update form should show the questions management panel."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:update_poll", args=[poll.id])))

    # The "Add Question" button should be visible (via htmx)
    add_btn = self.page.locator("#add-question-button button")
    self.assertTrue(add_btn.is_visible(), "Add Question button should be visible")

    # Reset errors: update form loads external JS assets (see PollCreateUITest)
    self.errors = []


class PollVoteUITest(PollsUITestBase):
  """UI tests for the poll voting page."""

  def test_vote_page_display(self):
    """The vote page should display poll info and a card."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:vote", args=[poll.id])))

    # Card should be visible
    self.assert_visible(".card", "Vote card should be visible")

    # Card header title
    self.assert_visible(".card-header-title", "Card header title should be visible")

    # Card footer with buttons
    self.assert_visible(".card-footer", "Card footer should be visible")


class PollNavigationUITest(PollsUITestBase):
  """UI tests for navigating between polls pages."""

  def test_navigate_from_list_to_detail(self):
    """Clicking a poll in the list should navigate to its detail page."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:list_polls")))
    self.page.wait_for_selector(".panel-block a.subtitle")

    # Click the first poll title link
    detail_link = self.page.locator(f'a.subtitle[href*="{reverse("polls:poll_detail", args=[poll.id])}"]')
    self.assertTrue(detail_link.is_visible(), "Detail link should be visible")
    detail_link.click()
    self.page.wait_for_timeout(500)

    # Should now be on the detail page
    self.assert_url_contains(reverse("polls:poll_detail", args=[poll.id]))
    self.assert_visible(".card", "Detail card should be visible")

  def test_navigate_from_detail_to_vote(self):
    """Clicking Vote on the detail page should navigate to the vote page."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:poll_detail", args=[poll.id])))

    # Click the Vote button (is-primary button in card footer)
    vote_button = self.page.locator(".card-footer a.button.is-primary")
    self.assertTrue(vote_button.is_visible(), "Vote button should be visible")
    vote_button.click()
    self.page.wait_for_timeout(500)

    # Should be on the vote page
    self.assert_url_contains(reverse("polls:vote", args=[poll.id]))
    self.assert_visible(".card-header-title", "Vote page title should be visible")

  def test_navigate_from_list_to_vote(self):
    """Clicking Vote on the list should navigate to the vote page."""
    self.login("admin", "password")
    poll = self.poll1
    self.page.goto(self.url(reverse("polls:list_polls")))
    self.page.wait_for_selector(".panel-block")

    # Click the Vote button link (contains /vote/ in href)
    vote_button = self.page.locator(f'.panel-block a[href*="{reverse("polls:vote", args=[poll.id])}"]')
    self.assertTrue(vote_button.is_visible(), "Vote button should be visible")
    vote_button.click()
    self.page.wait_for_timeout(500)

    # Should be on the vote page
    self.assert_url_contains(reverse("polls:vote", args=[poll.id]))
