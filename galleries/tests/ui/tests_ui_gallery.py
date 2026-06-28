from galleries.tests.factories import GalleryFactory

from .base import GalleryUITestBase


class GalleryListUITest(GalleryUITestBase):
  """UI tests for the gallery list/tree page."""

  def test_gallery_list_requires_auth(self):
    """The galleries page should redirect to login when not authenticated."""
    self.goto_page("galleries:galleries")
    self.assert_url_contains("/login/")

  def test_gallery_list_display(self):
    """The galleries list should display the gallery tree for authenticated users."""
    self.login_and_goto_page("galleries:galleries")

    # Panel heading contains the title
    self.assert_visible(".panel-heading", "Panel heading should be visible")
    # Our test gallery should appear in the tree
    self.assert_visible(f"text={self.gallery.name}", "Test gallery should be visible")

    # Create Gallery and Bulk Upload buttons
    self.assert_visible("a[href*='create']", "Create gallery link should be visible")
    self.assert_visible("a[href*='bulk_upload']", "Bulk upload link should be visible")
    self.errors.clear()

  def test_gallery_list_no_js_errors(self):
    """The galleries list should not produce JavaScript errors."""
    self.login_and_goto_page("galleries:galleries")
    self.page.wait_for_timeout(500)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class GalleryDetailUITest(GalleryUITestBase):
  """UI tests for the gallery detail page."""

  def test_gallery_detail_requires_auth(self):
    """The gallery detail page should redirect to login when not authenticated."""
    self.goto_page("galleries:detail", args=[self.gallery.slug])
    self.assert_url_contains("/login/")

  def test_gallery_detail_display(self):
    """The gallery detail should display the gallery name and photos."""
    self._goto_gallery_details()

    # Gallery name is in a span.title
    self.assert_visible("span.title", "Gallery title should be visible")
    self.assert_visible(f"text={self.gallery.name}", "Gallery name should be visible")

    # Photos should be displayed as thumbnails
    thumbnails = self.page.locator(".gallery-image")
    self.assertGreaterEqual(thumbnails.count(), 1, "At least one photo thumbnail should be visible")

    # Edit/Delete buttons should be visible (user is superuser)
    self.assert_visible("a[href*='/edit']", "Edit button should be visible")
    self.assert_visible("button[hx-get$='/delete']", "Delete button should be visible")
    self.errors.clear()

  def test_gallery_detail_pagination(self):
    """The gallery detail should paginate photos."""
    self._goto_gallery_details()

    # With 12 photos and DEFAULT_GALLERY_PAGE_SIZE (likely 10), we get 2 pages
    cards = self.page.locator(".gallery-image")
    self.assertEqual(cards.count(), 10, "First page should contain 10 gallery cards")

    # Check pagination is present (second pagination at bottom of page)
    # The paginate template uses nav.paginate
    page_links = self.page.locator("a.pagination-link")
    if page_links.count() > 0:
      page_link = page_links.get_by_text("2", exact=True).first
      if page_link.is_visible():
        page_link.click()
        self.page.wait_for_timeout(500)
        self.assertIn("/2", self.page.url, "Should navigate to page 2")

    self.errors.clear()

  def test_gallery_detail_no_js_errors(self):
    """The gallery detail should not produce JavaScript errors."""
    self._goto_gallery_details()
    self.page.wait_for_timeout(500)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class GalleryCreateUITest(GalleryUITestBase):
  """UI tests for the gallery creation form."""

  def test_gallery_create_requires_auth(self):
    """The gallery create page should redirect to login when not authenticated."""
    self.goto_page("galleries:create")
    self.assert_url_contains("/login/")

  def test_gallery_create_form_display(self):
    """The create gallery form should display all expected fields."""
    self.login_and_goto_page("galleries:create")

    # Title
    self.assert_visible("h1.title", "Form title should be visible")
    # Form fields (rendered via crispy-forms)
    self.assert_visible("input[name='name']", "Name input should be visible")
    self.assert_visible("select[name='parent']", "Parent gallery select should be visible")
    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.errors.clear()

  def test_gallery_create_submit(self):
    """Submitting the create form should create a new gallery."""
    self.login_and_goto_page("galleries:create")

    self.page.fill("input[name='name']", "Brand New Gallery")
    self.page.click("button[type='submit']")

    self.page.wait_for_timeout(1000)
    # After creation, should redirect to the new gallery detail
    self.assertIn("/galleries/", self.page.url)
    self.assert_visible("text=Brand New Gallery", "New gallery name should be visible")
    self.errors.clear()


class GalleryEditUITest(GalleryUITestBase):
  """UI tests for the gallery edit form."""

  def test_gallery_edit_requires_auth(self):
    """The gallery edit page should redirect to login when not authenticated."""
    self.goto_page("galleries:edit", args=[self.gallery.slug])
    self.assert_url_contains("/login/")

  def test_gallery_edit_form_display(self):
    """The edit gallery form should display with current values."""
    self.login_and_goto_page("galleries:edit", args=[self.gallery.slug])

    self.assert_visible("h1.title", "Form title should be visible")
    self.assert_visible("input[name='name']", "Name input should be visible")

    # The name field should be pre-filled with the gallery name
    name_input = self.page.locator("input[name='name']")
    self.assertEqual(
      name_input.input_value(),
      self.gallery.name,
      "Name input should be pre-filled with gallery name",
    )
    self.assert_visible("button[type='submit']", "Submit button should be visible")
    self.errors.clear()

  def test_gallery_edit_submit(self):
    """Submitting the edit form should update the gallery."""
    self.login_and_goto_page("galleries:edit", args=[self.gallery.slug])

    new_name = "Updated Gallery Name"
    name_input = self.page.locator("input[name='name']")
    name_input.fill(new_name)
    self.page.click("button[type='submit']")

    self.page.wait_for_timeout(1000)
    # Should redirect to the gallery detail with the new name
    self.assert_visible(f"text={new_name}", "Updated gallery name should be visible")
    self.errors.clear()


class GalleryDeleteUITest(GalleryUITestBase):
  """UI tests for gallery deletion."""

  def test_gallery_delete(self):
    """The gallery should be deletable via the confirm-delete modal."""
    # Create a gallery specifically for deletion
    delete_gallery = GalleryFactory(name="Gallery To Delete", create_photos=False, create_subgalleries=False)

    self.login_and_goto_page("galleries:detail", args=[delete_gallery.slug])
    self.page.wait_for_timeout(500)

    # Click the delete button to open the modal
    delete_button = self.page.locator("button[hx-get$='/delete']")
    self.assertTrue(delete_button.is_visible(), "Delete button should be visible")
    delete_button.click()
    self.page.wait_for_selector("#modal .modal", timeout=3000)
    self.assert_visible("#modal .modal", "Delete confirmation modal should appear")

    # Fill the confirmation field
    confirmation_input = self.page.locator("#modal input.confirmation_check")
    if confirmation_input.is_visible():
      confirmation_input.click()
      confirmation_input.press_sequentially(delete_gallery.name)
      self.page.wait_for_timeout(300)

    # Submit the deletion
    submit_button = self.page.locator("#modal button[type='submit']")
    self.assertTrue(submit_button.is_visible(), "Submit button in modal should be visible")
    submit_button.click()
    self.page.wait_for_timeout(1500)

    # Should be redirected to galleries list
    self.assertIn("/galleries/", self.page.url)
    self.errors.clear()
