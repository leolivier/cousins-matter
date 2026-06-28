from classified_ads.tests.factories import ClassifiedAdFactory

from .base import ClassifiedAdsUITestBase


class ClassifiedAdsListUITest(ClassifiedAdsUITestBase):
  """UI tests for the classified ads list page."""

  def test_list_requires_auth(self):
    """The classified ads list page should redirect to login when not authenticated."""
    self.goto_page("classified_ads:list")
    self.assert_url_contains("/login/")

  def test_list_display(self):
    """The classified ads list should display the title and ads for authenticated users."""
    self.login_and_goto_page("classified_ads:list")

    # Panel heading contains the title
    self.assert_visible(".panel-heading", "Panel heading should be visible")

    # Create Ad button should be visible
    self.assert_visible("a[href*='create']", "Create Ad button should be visible")

    # Ads should be displayed in panel blocks
    ad_blocks = self.page.locator(".panel-block")
    self.assertGreaterEqual(ad_blocks.count(), 2, "At least some ads should be displayed")
    self.errors.clear()

  def test_list_no_js_errors(self):
    """The classified ads list should not produce JavaScript errors."""
    self.login_and_goto_page("classified_ads:list")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class ClassifiedAdsCreateUITest(ClassifiedAdsUITestBase):
  """UI tests for the classified ad creation form."""

  def test_create_requires_auth(self):
    """The create ad page should redirect to login when not authenticated."""
    self.goto_page("classified_ads:create")
    self.assert_url_contains("/login/")

  def test_create_form_display(self):
    """The create ad form should display all expected fields."""
    self.login_and_goto_page("classified_ads:create")

    # Title
    self.assert_visible("h1.title", "Form title should be visible")

    # Form fields
    self.assert_visible("input[name='title']", "Title input should be visible")
    self.assert_visible("select[name='category']", "Category select should be visible")
    self.assert_visible("select[name='subcategory']", "Subcategory select should be visible")
    # Summernote initializes over the textarea, the editor div is the visible element
    self.assert_visible(".note-editor", "Summernote editor should be visible")
    self.assert_visible("select[name='shipping_method']", "Shipping method select should be visible")
    self.assert_visible("input[name='location']", "Location input should be visible")
    self.assert_visible("input[name='price']", "Price input should be visible")
    self.assert_visible("select[name='item_status']", "Item status select should be visible")

    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")

    # HTMX attribute on category for subcategory loading
    category_select = self.page.locator("select[name='category']")
    hx_get = category_select.get_attribute("hx-get")
    self.assertIsNotNone(hx_get, "Category select should have hx-get attribute for subcategories")

    # Gallery section placeholder (no photos before creation)
    self.assert_visible("#ad-photos", "Photos panel should be visible")

    self.errors.clear()

  def test_create_submit(self):
    """Submitting the create form should create a new classified ad."""
    self.login_and_goto_page("classified_ads:create")

    # Fill the form
    self.page.fill("input[name='title']", "My New Classified Ad")

    # Select a category — this triggers HTMX to populate subcategory
    self.page.select_option("select[name='category']", "vehicles")
    self.page.wait_for_timeout(500)

    # Select a subcategory
    self.page.select_option("select[name='subcategory']", "cars")

    # Fill description via the summernote editable div (the textarea is hidden by summernote)
    self.page.fill(".note-editable", "A great car in excellent condition.")

    # Fill price (required)
    self.page.fill("input[name='price']", "5000 €")

    # Submit the form
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to the detail page
    self.assertIn("/classified-ads/", self.page.url)
    self.assertIn("/detail", self.page.url)
    self.assert_visible("text=My New Classified Ad", "New ad title should be visible")

    self.errors.clear()


class ClassifiedAdsDetailUITest(ClassifiedAdsUITestBase):
  """UI tests for the classified ad detail page."""

  def test_detail_requires_auth(self):
    """The ad detail page should redirect to login when not authenticated."""
    self.goto_page("classified_ads:detail", args=[self.ad.pk])
    self.assert_url_contains("/login/")

  def test_detail_display(self):
    """The ad detail page should display all ad information for authenticated users."""
    self.login_and_goto_page("classified_ads:detail", args=[self.ad.pk])

    # Panel contains the ad title (use direct child to avoid the photos panel-heading inside nav.panel)
    self.assert_visible(".container > .panel > .panel-heading", "Panel heading should be visible")
    self.assert_visible(f"text={self.ad.title}", "Ad title should be visible")

    # Category, subcategory, item status grids (two .fixed-grid elements on the page)
    grids = self.page.locator(".fixed-grid")
    self.assertGreaterEqual(grids.count(), 2, "At least two info grids should be visible")

    # Description content (inside a panel-block)
    self.assert_visible(".panel-block .content", "Description content should be visible")

    # Price should be displayed
    self.assert_visible(f"text={self.ad.price}", "Price should be visible")

    # Photos panel
    self.assert_visible("#ad-photos", "Photos panel should be visible")

    self.errors.clear()

  def test_detail_owner_buttons(self):
    """The ad owner should see edit and delete buttons on the detail page."""
    self.login_and_goto_page("classified_ads:detail", args=[self.ad.pk])

    # Update Ad button (owner only)
    self.assert_visible("a[href*='/update']", "Update Ad button should be visible for owner")

    # Delete button (owner only) — hx-get on the delete URL
    self.assert_visible("button[hx-get*='/delete']", "Delete button should be visible for owner")

    self.errors.clear()

  def test_detail_non_owner_buttons(self):
    """A non-owner user should see the send message button instead of edit/delete."""
    # Login as the other user
    self.login("otheruser", "password")
    self.goto_page("classified_ads:detail", args=[self.ad.pk])

    # Send message button should be visible for non-owner
    send_msg_button = self.page.locator("button[hx-get*='/send-message']")
    self.assertTrue(send_msg_button.is_visible(), "Send message button should be visible for non-owner")

    # Update and Delete buttons should NOT be visible
    update_button = self.page.locator("a[href*='/update']")
    self.assertEqual(update_button.count(), 0, "Update button should not be visible for non-owner")

    self.errors.clear()

  def test_detail_no_js_errors(self):
    """The ad detail page should not produce JavaScript errors."""
    self.login_and_goto_page("classified_ads:detail", args=[self.ad.pk])
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors: {self.errors}")


class ClassifiedAdsUpdateUITest(ClassifiedAdsUITestBase):
  """UI tests for the classified ad update form."""

  def test_update_requires_auth(self):
    """The update ad page should redirect to login when not authenticated."""
    self.goto_page("classified_ads:update", args=[self.ad.pk])
    self.assert_url_contains("/login/")

  def test_update_form_display(self):
    """The update ad form should display with pre-filled current values."""
    self.login_and_goto_page("classified_ads:update", args=[self.ad.pk])

    # Title
    self.assert_visible("h1.title", "Form title should be visible")

    # The title field should be pre-filled
    title_input = self.page.locator("input[name='title']")
    self.assertEqual(
      title_input.input_value(),
      self.ad.title,
      "Title input should be pre-filled with ad title",
    )

    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")

    self.errors.clear()

  def test_update_submit(self):
    """Submitting the update form should update the ad."""
    self.login_and_goto_page("classified_ads:update", args=[self.ad.pk])

    # Change the title
    new_title = "Updated Classified Ad Title"
    title_input = self.page.locator("input[name='title']")
    title_input.fill(new_title)

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to the detail page with the new title
    self.assert_visible(f"text={new_title}", "Updated ad title should be visible")

    self.errors.clear()


class ClassifiedAdsDeleteUITest(ClassifiedAdsUITestBase):
  """UI tests for classified ad deletion."""

  def test_delete_confirmation_modal(self):
    """Clicking the delete button should open a confirmation modal."""
    self.login_and_goto_page("classified_ads:detail", args=[self.ad.pk])

    # Click the delete button to open the modal
    delete_button = self.page.locator("button[hx-get*='/delete']")
    self.assertTrue(delete_button.is_visible(), "Delete button should be visible")
    delete_button.click()

    # Wait for the modal to appear
    self.page.wait_for_selector("#modal .modal", timeout=3000)
    self.assert_visible("#modal .modal", "Delete confirmation modal should appear")

    # The confirmation input should be visible (since expected_value=ad.title)
    confirmation_input = self.page.locator("#modal input.confirmation_check")
    self.assertTrue(confirmation_input.is_visible(), "Confirmation input should be visible")

    self.errors.clear()

  def test_delete_submit(self):
    """Confirming the deletion should remove the ad and redirect to the list."""
    # Create an ad specifically for deletion
    delete_ad = ClassifiedAdFactory(
      title="Ad To Delete",
      owner=self.user,
      category="vehicles",
      subcategory="cars",
      create_photos=False,
    )

    self.login_and_goto_page("classified_ads:detail", args=[delete_ad.pk])
    self.page.wait_for_timeout(500)

    # Click the delete button
    delete_button = self.page.locator("button[hx-get*='/delete']")
    delete_button.click()
    self.page.wait_for_selector("#modal .modal", timeout=3000)

    # Fill the confirmation field with the ad title
    confirmation_input = self.page.locator("#modal input.confirmation_check")
    confirmation_input.click()
    confirmation_input.press_sequentially(delete_ad.title)
    self.page.wait_for_timeout(300)

    # Submit the deletion
    submit_button = self.page.locator("#modal button[type='submit']")
    self.assertTrue(submit_button.is_visible(), "Submit button in modal should be visible")
    submit_button.click()
    self.page.wait_for_timeout(1500)

    # Should be redirected to the classified ads list
    self.assertIn("/classified-ads/", self.page.url)
    # The list URL should not contain the deleted ad's pk
    self.assertNotIn(str(delete_ad.pk), self.page.url)

    self.errors.clear()


class ClassifiedAdsPhotoUITest(ClassifiedAdsUITestBase):
  """UI tests for classified ad photo management."""

  def test_add_photo_modal_for_owner(self):
    """The ad owner should see the add photo button that opens a modal."""
    self.login_and_goto_page("classified_ads:detail", args=[self.ad.pk])

    # Add photo button should be visible for the owner
    add_photo_button = self.page.locator("button[hx-get*='/photo']")
    self.assertTrue(add_photo_button.is_visible(), "Add photo button should be visible for owner")

    # Click the add photo button to open the modal
    add_photo_button.click()
    self.page.wait_for_selector("#modal .modal", timeout=3000)
    self.assert_visible("#modal .modal", "Add photo modal should appear")

    # The modal should contain a file input
    self.assert_visible("#modal input[type='file']", "File input should be visible in the modal")

    # Cancel button should be visible
    self.assert_visible("#modal button[type='button']", "Cancel button should be visible")

    self.errors.clear()

  def test_no_photo_message_for_new_ad(self):
    """The create form should show a message that photos can be added after creation."""
    self.login_and_goto_page("classified_ads:create")

    # The message about adding photos after creation should be visible
    self.assert_visible("#ad-photos .content", "Photos placeholder message should be visible")

    self.errors.clear()


class ClassifiedAdsMessageUITest(ClassifiedAdsUITestBase):
  """UI tests for the send message feature."""

  def test_send_message_modal_for_non_owner(self):
    """A non-owner should be able to open the send message modal."""
    # Login as the other user
    self.login("otheruser", "password")
    self.goto_page("classified_ads:detail", args=[self.ad.pk])

    # Click the send message button
    send_msg_button = self.page.locator("button[hx-get*='/send-message']")
    self.assertTrue(send_msg_button.is_visible(), "Send message button should be visible")
    send_msg_button.click()

    # Wait for the modal to appear
    self.page.wait_for_selector("#modal .modal", timeout=3000)
    self.assert_visible("#modal .modal", "Send message modal should appear")

    # The modal should contain a textarea for the message
    self.assert_visible("#modal textarea", "Message textarea should be visible in the modal")

    # Submit button should be visible in the modal
    self.assert_visible("#modal button[type='submit']", "Submit button should be visible in the modal")

    self.errors.clear()
