import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from django.urls import reverse

from .base import TroveUITestBase


class TroveAppUITest(TroveUITestBase):
  """UI tests exercising the main troves flows.

  Covers:
  * Trove list page with category filtering
  * Trove creation via the form
  * Trove update (edit) form
  * Trove detail page
  * Trove deletion via HTMX
  """

  def test_trove_cave_lists_all_troves(self):
    """The trove cave should display all created troves."""
    self.login("admin", "password")
    self.page.goto(self.url(reverse("troves:list")))
    self.page.wait_for_selector(".cell")

    cells = self.page.locator(".cell")
    self.assertEqual(cells.count(), len(self.troves), f"Should display all {len(self.troves)} troves")

    # Check that trove titles are visible
    for trove in self.troves:
      self.assert_visible(f"#trove-{trove.id}", f"Trove {trove.id} should be visible")

  def test_trove_cave_filter_by_category(self):
    """The category dropdown should filter troves."""
    self.login("admin", "password")
    self.page.goto(self.url(reverse("troves:list")))
    self.page.wait_for_selector(".cell")

    # Select "history" category
    dropdown = self.page.locator('select[name="category"]')
    dropdown.select_option("history")

    # Wait for page reload after form auto-submit
    self.page.wait_for_selector(".cell")

    cells = self.page.locator(".cell")
    # Only the history trove should be visible
    self.assertEqual(cells.count(), 1, "Only the history trove should be displayed")
    history_trove = self.troves[0]  # First trove is "history"
    self.assert_visible(f"#trove-{history_trove.id}")

    # Select "recipes" category
    dropdown.select_option("recipes")
    self.page.wait_for_selector(".cell")
    cells = self.page.locator(".cell")
    self.assertEqual(cells.count(), 1, "Only the recipes trove should be displayed")

    # Select "all" to reset
    dropdown.select_option("all")
    self.page.wait_for_selector(".cell")
    cells = self.page.locator(".cell")
    self.assertEqual(cells.count(), len(self.troves), "All troves should be back")

  def test_trove_cave_shows_add_button_for_logged_user(self):
    """The 'Add a treasure' button should be visible for logged-in users."""
    self.login("admin", "password")
    self.page.goto(self.url(reverse("troves:list")))
    self.page.wait_for_selector(".cell")

    add_button = self.page.locator(f'a[href="{reverse("troves:create")}"]')
    self.assertTrue(add_button.is_visible(), "Add treasure button should be visible")

  def test_create_treasure_form_display(self):
    """The creation form should be accessible and display correctly."""
    self.login("admin", "password")
    self.page.goto(self.url(reverse("troves:create")))
    self.page.wait_for_selector("#treasure-form")

    # The form should have the expected fields
    self.assert_visible('input[name="title"]', "Title input should be visible")
    self.assert_visible('select[name="category"]', "Category select should be visible")
    self.assert_visible('input[name="picture"]', "Picture file input should be visible")
    self.assert_visible('input[name="file"]', "File input should be visible")

    # Submit and Cancel buttons
    self.assert_visible('button[type="submit"]', "Submit button should be visible")
    # Use aria-label to target only the Cancel link, not the navbar link
    cancel_link = self.page.locator('a[aria-label="close"]')
    self.assertTrue(cancel_link.is_visible(), "Cancel link should be visible")

  def test_update_treasure_form_display(self):
    """The update form should load with existing treasure data."""
    self.login("admin", "password")
    trove = self.troves[0]
    self.page.goto(self.url(reverse("troves:update", args=[trove.id])))
    self.page.wait_for_selector("#treasure-form")

    # The title input should be pre-filled
    title_input = self.page.locator('input[name="title"]')
    self.assertEqual(
      title_input.input_value(),
      trove.title,
      "Title input should contain the existing title",
    )

    self.assert_visible('button[type="submit"]', "Submit button should be visible")

  def test_treasure_detail_page(self):
    """The detail page should display all treasure information."""
    self.login("admin", "password")
    trove = self.troves[0]
    self.page.goto(self.url(reverse("troves:detail", args=[trove.id])))
    self.page.wait_for_selector(".card")

    # The card should contain the trove title
    self.assert_visible(f"text={trove.title}", "Trove title should be visible")

    # The card should contain an image
    self.assert_visible(".card-image img", "Treasure image should be visible")

    # Owner avatar should be visible
    self.assert_visible(".media-left img", "Owner avatar should be visible")

  def test_delete_treasure_via_htmx(self):
    """Clicking the delete button should remove the trove cell via HTMX."""
    self.login("admin", "password")
    trove = self.troves[0]
    self.page.goto(self.url(reverse("troves:list")))
    self.page.wait_for_selector(f"#trove-{trove.id}")

    # Auto-accept the confirm dialog triggered by hx-confirm
    self.page.on("dialog", lambda dialog: dialog.accept())

    # Click the HTMX delete button inside the trove cell
    delete_button = self.page.locator(f"#trove-{trove.id} a[hx-post]")
    self.assertTrue(delete_button.is_visible(), "Delete button should be visible")
    delete_button.click()

    # The trove cell should be removed from the DOM (hx-swap="delete")
    self.page.wait_for_selector(f"#trove-{trove.id}", state="detached", timeout=3000)
    self.assertTrue(
      self.page.locator(f"#trove-{trove.id}").count() == 0,
      "Deleted trove cell should no longer be in the DOM",
    )

  def test_navigation_from_list_to_detail(self):
    """Clicking a trove link in the list should navigate to the detail page."""
    self.login("admin", "password")
    trove = self.troves[0]
    self.page.goto(self.url(reverse("troves:list")))
    self.page.wait_for_selector(f"#trove-{trove.id}")

    # Click the link to the detail page
    detail_link = self.page.locator(f'#trove-{trove.id} a[href*="{reverse("troves:detail", args=[trove.id])}"]')
    self.assertTrue(detail_link.is_visible(), "Detail link should be visible")
    detail_link.click()

    # Should now be on the detail page
    self.page.wait_for_selector(".card-image", state="visible")
    self.assert_url_contains(reverse("troves:detail", args=[trove.id]))
