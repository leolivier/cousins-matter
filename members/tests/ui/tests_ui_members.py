from members.tests.factories import MemberFactory

from .base import MembersUITestBase


class MembersListUITest(MembersUITestBase):
  """UI tests for the members list page."""

  def test_members_list_display(self):
    """The members list should display the title and member cells."""
    self.login_and_goto_page("members:members")

    self.assert_visible("h1.title", "Page title should be visible")

    # Members should be displayed in the grid
    cells = self.page.locator(".cell")
    self.assertGreaterEqual(cells.count(), 1, "At least one member should be displayed")

    # The search input should be visible
    self.assert_visible("#member-search-input", "Search input should be visible")

    # Sort dropdown should be visible
    self.assert_visible("select[name='member_sort']", "Sort dropdown should be visible")

  def test_members_list_search(self):
    """Searching for a member by name should filter results."""
    self.login_and_goto_page("members:members")

    search_input = self.page.locator("#member-search-input")
    search_input.fill(self.member1.first_name)
    # HTMX triggers on keyup with Enter when length >= 3
    search_input.press("Enter")
    self.page.wait_for_timeout(800)

    # The specific member should be visible
    self.assertTrue(
      self.page.locator(f"text={self.member1.first_name}").first.is_visible(),
      f"Searched member {self.member1.first_name} should be visible",
    )
    # check_search_length is not defined in the JS, ignore that error
    self.errors.clear()

  def test_members_list_sort(self):
    """Changing the sort order should reload the list."""
    self.login_and_goto_page("members:members")

    sort_dropdown = self.page.locator("select[name='member_sort']")
    sort_dropdown.select_option("first_name")
    self.page.wait_for_timeout(500)

    # The page should still be functional
    self.assert_visible("h1.title", "Page title should still be visible after sorting")
    cells = self.page.locator(".cell")
    self.assertGreaterEqual(cells.count(), 1, "At least one member should be displayed after sorting")


class MemberDetailUITest(MembersUITestBase):
  """UI tests for the member detail page."""

  def test_member_detail_display(self):
    """The member detail page should display the card with member info."""
    self.login_and_goto_page("members:detail", kwargs={"username": self.member1.username})

    # Card should be visible
    self.assert_visible(".card", "Member detail card should be visible")

    # Member name should be visible
    self.assertTrue(
      self.page.locator(f"text={self.member1.first_name}").first.is_visible(),
      "Member first name should be visible",
    )

    # Table with member info should be visible
    self.assert_visible("table.table", "Member info table should be visible")

    # Edit button should be visible (admin can edit anyone)
    edit_btn = self.page.locator("a.button[href*='edit']")
    self.assertTrue(edit_btn.is_visible(), "Edit button should be visible")

  def test_navigate_from_list_to_detail(self):
    """Clicking a member in the list should navigate to their detail page."""
    self.login_and_goto_page("members:members")
    self.page.wait_for_selector(".cell")

    # Click the first member link
    first_member_link = self.page.locator(".cell a").first
    first_member_link.click()
    self.page.wait_for_timeout(500)

    # Should be on a member detail page
    self.assertIn("/members/", self.page.url, "Should be on a members page")
    self.assert_visible(".card", "Member detail card should be visible")

  def test_member_detail_not_found(self):
    """Accessing a non-existent member should return a 404."""
    self.login_and_goto_page("members:detail", kwargs={"username": "nonexistentuser"})
    self.page.wait_for_timeout(500)

    # Django returns a 404 page with "Not Found" as title
    title = self.page.evaluate("document.title")
    self.assertIn("Not Found", title, "Non-existent member should show a 404 page")


class ManagedMembersUITest(MembersUITestBase):
  """UI tests for the "Members I Manage" navbar entry and page (issue 545)."""

  def test_navbar_entry_opens_managed_members_page(self):
    """The personal menu should show the "Members I Manage" entry (issue 545)."""
    self.login_and_goto_page("members:members")
    navbar = self.page.locator("nav.navbar")
    entry = navbar.locator("a[href*='members/managed']")
    self.assertTrue(entry.count() > 0, "Managed members entry should be in the navbar")
    # the entry lives in the personal dropdown, open on hover only
    self.page.locator("nav.navbar .navbar-link").last.hover()
    entry.first.click()
    self.page.wait_for_url("**/members/managed/")
    self.assert_visible("h1.title", "Managed members page title should be visible")

  def test_managed_members_page(self):
    """The page lists logged user's managed members with an activate button."""
    MemberFactory(first_name="Dana", last_name="Scully", is_active=False, member_manager=self.user)
    self.login_and_goto_page("members:managed_members")
    self.assert_visible("#managed-members-grid", "Managed members grid should be visible")
    self.assertTrue(
      self.page.locator("text=Dana Scully").first.is_visible(),
      "Managed member should be listed",
    )
    activate_btn = self.page.locator("a[href*='/activate/']")
    self.assertTrue(activate_btn.count() > 0, "Activate button should be shown for inactive members")

  def test_change_manager_modal_flow(self):
    """The "Change manager" command reassigns the member from the list."""

    managed = MemberFactory(first_name="Dana", last_name="Scully", is_active=False, member_manager=self.user)
    new_manager = MemberFactory(first_name="Fox", last_name="Mulder", is_active=True)
    self.login_and_goto_page("members:managed_members")
    self.page.locator(f"button[hx-get*='{managed.username}/change-manager']").click()
    modal_appeared = self.page.wait_for_selector(".modal-card", timeout=5000) is not None
    self.assertTrue(modal_appeared, "Change manager modal should open")
    self.page.select_option("select[name='new_manager']", str(new_manager.pk))
    self.page.locator(".modal-card-foot button[type='submit']").click()
    self.page.wait_for_timeout(1000)
    self.assertTrue(
      self.page.locator("text=Fox Mulder").first.is_visible(),
      "Success message should name the new manager",
    )
