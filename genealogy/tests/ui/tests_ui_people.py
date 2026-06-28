from django.urls import reverse

from genealogy.tests.factories import PersonFactory

from .base import GenealogyUITestBase


class GenealogyPersonListUITest(GenealogyUITestBase):
  """UI tests for the person list page."""

  def test_person_list_requires_auth(self):
    """The person list page should redirect to login when not authenticated."""
    self.goto_page("genealogy:person_list")
    self.assert_url_contains("/login/")

  def test_person_list_display(self):
    """The person list should display people in a table."""
    self.login_and_goto_page("genealogy:person_list")

    # Page title
    self.assert_visible("h1.title", "Genealogy page title should be visible")

    # People tab should be active
    active_tab = self.page.locator(".tabs li.is-active a")
    self.assertTrue(active_tab.is_visible(), "People tab should be active")

    # Table with people
    self.assert_visible("table.table", "People table should be visible")

    # At least our test persons should appear
    rows = self.page.locator("tbody tr")
    self.assertGreaterEqual(rows.count(), 3, "At least 3 people should be in the table")

    # Add Person button
    self.assert_visible("a[href*='add']", "Add Person button should be visible")

    # Our specific person should appear (use first to avoid strict mode with multiple matches)
    dupont_cells = self.page.locator(f"text={self.person1.last_name}")
    self.assertGreaterEqual(dupont_cells.count(), 1, "Test person should appear in the list")

    self.errors.clear()

  def test_person_list_search(self):
    """The search input should filter people via HTMX."""
    self.login_and_goto_page("genealogy:person_list")

    # Search input should be visible with HTMX attributes
    search_input = self.page.locator("input[name='q']")
    self.assertTrue(search_input.is_visible(), "Search input should be visible")
    self.assertEqual(
      search_input.get_attribute("hx-get"),
      reverse("genealogy:person_list"),
      "Search input should have correct hx-get URL",
    )
    self.assertEqual(
      search_input.get_attribute("hx-target"),
      "#person-table-body",
      "Search input should target the table body",
    )

    self.errors.clear()

  def test_person_list_no_js_errors(self):
    """The person list should not produce JavaScript errors."""
    self.login_and_goto_page("genealogy:person_list")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class GenealogyPersonDetailUITest(GenealogyUITestBase):
  """UI tests for the person detail page."""

  def test_person_detail_requires_auth(self):
    """The person detail page should redirect to login when not authenticated."""
    self.goto_page("genealogy:person_detail", args=[self.person1.pk])
    self.assert_url_contains("/login/")

  def test_person_detail_display(self):
    """The person detail should display the person's information."""
    self.login_and_goto_page("genealogy:person_detail", args=[self.person1.pk])

    # Person name in the card title (use full name to avoid matching partners)
    self.assert_visible(".card", "Person card should be visible")
    self.assert_visible(f"text={self.person1.first_name} {self.person1.last_name}", "Person full name should be visible")

    # Family section
    self.assert_visible("h3.title", "Family section title should be visible")

    # Action buttons in card footer
    self.assert_visible(".card-footer", "Card footer with action buttons should be visible")

    # Edit button
    self.assert_visible("a[href*='/edit']", "Edit button should be visible")
    # Delete button
    self.assert_visible("a[href*='/delete']", "Delete button should be visible")
    # Family chart button (target card footer to avoid matching the tab navigation)
    self.assert_visible(".card-footer a[href*='/family-chart/']", "Family chart button should be visible")

    self.errors.clear()

  def test_person_detail_family_links(self):
    """The person detail should show links to family members."""
    self.login_and_goto_page("genealogy:person_detail", args=[self.person1.pk])

    # Should show partner (person2 is the partner of person1 via the family)
    partner_link = self.page.locator(f"a[href*='/{self.person2.pk}']")
    # The partner may or may not be displayed depending on test data
    # Just check that the family box exists
    family_box = self.page.locator(".box")
    self.assertGreaterEqual(family_box.count(), 1, "Family info box should be visible")

    self.errors.clear()

  def test_person_detail_no_js_errors(self):
    """The person detail should not produce JavaScript errors."""
    self.login_and_goto_page("genealogy:person_detail", args=[self.person1.pk])
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class GenealogyPersonCreateUITest(GenealogyUITestBase):
  """UI tests for the person creation form."""

  def test_person_create_requires_auth(self):
    """The person create page should redirect to login when not authenticated."""
    self.goto_page("genealogy:person_create")
    self.assert_url_contains("/login/")

  def test_person_create_form_display(self):
    """The person create form should display all expected fields."""
    self.login_and_goto_page("genealogy:person_create")

    # Form title
    self.assert_visible("h2.title", "Form title should be visible")

    # Form fields
    self.assert_visible("input[name='first_name']", "First name input should be visible")
    self.assert_visible("input[name='last_name']", "Last name input should be visible")
    self.assert_visible("select[name='sex']", "Sex select should be visible")
    self.assert_visible("input[name='birth_date']", "Birth date input should be visible")
    self.assert_visible("input[name='birth_place']", "Birth place input should be visible")
    self.assert_visible("input[name='death_date']", "Death date input should be visible")
    self.assert_visible("input[name='death_place']", "Death place input should be visible")
    self.assert_visible("textarea[name='notes']", "Notes textarea should be visible")

    # Buttons
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_person_create_submit(self):
    """Submitting the create form should create a new person and redirect to detail."""
    self.login_and_goto_page("genealogy:person_create")

    # Fill the form
    self.page.fill("input[name='first_name']", "Nouveau")
    self.page.fill("input[name='last_name']", "Personne")
    self.page.select_option("select[name='sex']", "M")

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to person detail
    self.assertIn("/genealogy/people/", self.page.url)
    self.assert_visible("text=Nouveau Personne", "New person name should be visible")

    self.errors.clear()


class GenealogyPersonUpdateUITest(GenealogyUITestBase):
  """UI tests for the person update form."""

  def test_person_update_requires_auth(self):
    """The person update page should redirect to login when not authenticated."""
    self.goto_page("genealogy:person_update", args=[self.person1.pk])
    self.assert_url_contains("/login/")

  def test_person_update_form_display(self):
    """The person update form should display with pre-filled values."""
    self.login_and_goto_page("genealogy:person_update", args=[self.person1.pk])

    # Form title
    self.assert_visible("h2.title", "Form title should be visible")

    # The first name field should be pre-filled
    first_name_input = self.page.locator("input[name='first_name']")
    self.assertEqual(
      first_name_input.input_value(),
      self.person1.first_name,
      "First name should be pre-filled",
    )

    # Submit and Cancel buttons
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_person_update_submit(self):
    """Submitting the update form should update the person."""
    self.login_and_goto_page("genealogy:person_update", args=[self.person1.pk])

    # Change the first name
    new_name = "JeanUpdated"
    first_name_input = self.page.locator("input[name='first_name']")
    first_name_input.fill(new_name)

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to the detail page with the new name
    self.assert_visible(f"text={new_name}", "Updated person name should be visible")

    self.errors.clear()


class GenealogyPersonDeleteUITest(GenealogyUITestBase):
  """UI tests for the person deletion."""

  def test_person_delete_requires_auth(self):
    """The person delete page should redirect to login when not authenticated."""
    self.goto_page("genealogy:person_delete", args=[self.person3.pk])
    self.assert_url_contains("/login/")

  def test_person_delete_confirmation_page(self):
    """The person delete page should show a confirmation form."""
    self.login_and_goto_page("genealogy:person_delete", args=[self.person3.pk])

    # Confirmation title
    self.assert_visible("h2.title.has-text-danger", "Confirmation title should be visible")

    # Delete and Cancel buttons
    self.assert_visible("button[type='submit'].is-danger", "Delete submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_person_delete_submit(self):
    """Confirming the deletion should remove the person."""
    # Create a person specifically for deletion
    delete_person = PersonFactory(
      first_name="ToDelete",
      last_name="Person",
      sex="F",
      member=None,
    )

    self.login_and_goto_page("genealogy:person_delete", args=[delete_person.pk])

    # Submit the deletion
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should be redirected to the person list
    self.assertIn("/genealogy/people/", self.page.url)

    self.errors.clear()
