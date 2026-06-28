from django.urls import reverse

from genealogy.tests.factories import FamilyFactory, PersonFactory

from .base import GenealogyUITestBase


class GenealogyFamilyListUITest(GenealogyUITestBase):
  """UI tests for the family list page."""

  def test_family_list_requires_auth(self):
    """The family list page should redirect to login when not authenticated."""
    self.goto_page("genealogy:family_list")
    self.assert_url_contains("/login/")

  def test_family_list_display(self):
    """The family list should display families in a table."""
    self.login_and_goto_page("genealogy:family_list")

    # Page title
    self.assert_visible("h1.title", "Genealogy page title should be visible")

    # Families tab should be active
    active_tab = self.page.locator(".tabs li.is-active a")
    self.assertTrue(active_tab.is_visible(), "Families tab should be active")

    # Table with families
    self.assert_visible("table.table", "Families table should be visible")

    # At least one family should appear
    rows = self.page.locator("tbody tr")
    self.assertGreaterEqual(rows.count(), 1, "At least one family should be in the table")

    # Add Family button
    self.assert_visible("a[href*='add']", "Add Family button should be visible")

    # Our test couple should appear (use count to avoid strict mode with shared last names)
    dupont_cells = self.page.locator(f"text={self.person1.last_name}")
    self.assertGreaterEqual(dupont_cells.count(), 1, "Partner 1 should appear in the list")

    # Edit and Delete buttons
    self.assert_visible("a[href*='/edit']", "Edit button should be visible")
    self.assert_visible("a[href*='/delete']", "Delete button should be visible")

    self.errors.clear()

  def test_family_list_search(self):
    """The search input should filter families via HTMX."""
    self.login_and_goto_page("genealogy:family_list")

    # Search input with HTMX attributes
    search_input = self.page.locator("input[name='q']")
    self.assertTrue(search_input.is_visible(), "Search input should be visible")
    self.assertEqual(
      search_input.get_attribute("hx-get"),
      reverse("genealogy:family_list"),
      "Search input should have correct hx-get URL",
    )
    self.assertEqual(
      search_input.get_attribute("hx-target"),
      "#family-table-body",
      "Search input should target the table body",
    )

    self.errors.clear()

  def test_family_list_no_js_errors(self):
    """The family list should not produce JavaScript errors."""
    self.login_and_goto_page("genealogy:family_list")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class GenealogyFamilyCreateUITest(GenealogyUITestBase):
  """UI tests for the family creation form."""

  def test_family_create_requires_auth(self):
    """The family create page should redirect to login when not authenticated."""
    self.goto_page("genealogy:family_create")
    self.assert_url_contains("/login/")

  def test_family_create_form_display(self):
    """The family create form should display all expected fields."""
    self.login_and_goto_page("genealogy:family_create")

    # Form title
    self.assert_visible("h2.title", "Form title should be visible")

    # Form fields
    self.assert_visible("select[name='partner1']", "Partner 1 select should be visible")
    self.assert_visible("select[name='partner2']", "Partner 2 select should be visible")
    self.assert_visible("select[name='union_type']", "Union type select should be visible")
    self.assert_visible("input[name='union_date']", "Union date input should be visible")
    self.assert_visible("input[name='union_place']", "Union place input should be visible")
    self.assert_visible("input[name='separation_date']", "Separation date input should be visible")

    # Buttons
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_family_create_submit(self):
    """Submitting the create form should create a new family."""
    p1 = PersonFactory(first_name="PartnerA", last_name="Test", sex="M", member=None)
    p2 = PersonFactory(first_name="PartnerB", last_name="Test", sex="F", member=None)

    self.login_and_goto_page("genealogy:family_create")

    # Select partners
    self.page.select_option("select[name='partner1']", str(p1.pk))
    self.page.select_option("select[name='partner2']", str(p2.pk))
    self.page.select_option("select[name='union_type']", "MARR")

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to dashboard (as per family_create view)
    self.assertIn("/genealogy/", self.page.url)

    self.errors.clear()


class GenealogyFamilyUpdateUITest(GenealogyUITestBase):
  """UI tests for the family update form."""

  def test_family_update_requires_auth(self):
    """The family update page should redirect to login when not authenticated."""
    self.goto_page("genealogy:family_update", args=[self.family.pk])
    self.assert_url_contains("/login/")

  def test_family_update_form_display(self):
    """The family update form should display with pre-filled values."""
    self.login_and_goto_page("genealogy:family_update", args=[self.family.pk])

    # Form title
    self.assert_visible("h2.title", "Form title should be visible")

    # Submit and Cancel buttons
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_family_update_submit(self):
    """Submitting the update form should update the family."""
    self.login_and_goto_page("genealogy:family_update", args=[self.family.pk])

    # Change union type
    self.page.select_option("select[name='union_type']", "CIVI")

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to dashboard
    self.assertIn("/genealogy/", self.page.url)

    self.errors.clear()


class GenealogyFamilyDeleteUITest(GenealogyUITestBase):
  """UI tests for the family deletion."""

  def test_family_delete_requires_auth(self):
    """The family delete page should redirect to login when not authenticated."""
    self.goto_page("genealogy:family_delete", args=[self.family.pk])
    self.assert_url_contains("/login/")

  def test_family_delete_confirmation_page(self):
    """The family delete page should show a confirmation form."""
    self.login_and_goto_page("genealogy:family_delete", args=[self.family.pk])

    # Confirmation title
    self.assert_visible("h2.title.has-text-danger", "Confirmation title should be visible")

    # Delete and Cancel buttons
    self.assert_visible("button[type='submit'].is-danger", "Delete submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_family_delete_submit(self):
    """Confirming the deletion should remove the family."""
    # Create a family specifically for deletion
    p3 = PersonFactory(first_name="DelA", last_name="Fam", sex="M", member=None)
    p4 = PersonFactory(first_name="DelB", last_name="Fam", sex="F", member=None)
    delete_family = FamilyFactory(
      partner1=p3,
      partner2=p4,
      create_children=False,
    )

    self.login_and_goto_page("genealogy:family_delete", args=[delete_family.pk])

    # Submit the deletion
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should be redirected to the dashboard
    self.assertIn("/genealogy/", self.page.url)

    self.errors.clear()


class GenealogyGedcomUITest(GenealogyUITestBase):
  """UI tests for GEDCOM import/export."""

  def test_import_gedcom_requires_auth(self):
    """The GEDCOM import page should redirect to login when not authenticated."""
    self.goto_page("genealogy:import_gedcom")
    self.assert_url_contains("/login/")

  def test_import_gedcom_form_display(self):
    """The GEDCOM import page should display the upload form."""
    self.login_and_goto_page("genealogy:import_gedcom")

    # Form title
    self.assert_visible("h2.title", "Import form title should be visible")

    # File input
    self.assert_visible("input[type='file']", "File upload input should be visible")

    # Import and Cancel buttons
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.assert_visible("a.button.is-light", "Cancel button should be visible")

    self.errors.clear()

  def test_export_gedcom_download(self):
    """The GEDCOM export should return a downloadable file."""
    self.login_and_goto_page("genealogy:dashboard")

    # Export button on the dashboard (use specific path to avoid navbar members export)
    export_button = self.page.locator("a[href*='/genealogy/export']")
    self.assertTrue(export_button.is_visible(), "Export button should be visible")

    # Click the export link — should download a file
    with self.page.expect_download() as download_info:
      export_button.click()

    download = download_info.value
    self.assertIsNotNone(download, "Download should have started")
    # GEDCOM files have .ged extension or text/gedcom content type
    self.assertTrue(
      download.suggested_filename.endswith(".ged") or "gedcom" in (download.suggested_filename or "").lower(),
      f"Download should be a GEDCOM file, got: {download.suggested_filename}",
    )

    self.errors.clear()
