import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from .base import ForumUITestBase


class CommentUITest(ForumUITestBase):
  """UI tests for comment creation, editing and deletion via HTMX."""

  def test_add_comment_link_visible(self):
    """The add comment link should be visible on the post detail page."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    add_link = self.page.locator("a[hx-get*='/comments']")
    self.assertTrue(add_link.first.is_visible(), "Add comment link should be visible")

  def test_add_comment_form_loads_via_htmx(self):
    """Clicking the add comment link should load the comment form via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    first_message_id = self.post.first_message.id
    add_link = self.page.locator(f"a[hx-get*='/comments'][hx-target='#create-comment-{first_message_id}']")
    add_link.click()
    self.page.wait_for_timeout(500)

    form = self.page.locator(f"#create-comment-{first_message_id} form.comment-form")
    self.assertTrue(form.is_visible(), "Comment form should appear after clicking add link")

  def test_add_comment_submit_via_htmx(self):
    """Submitting the comment form should add a new comment via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    first_message_id = self.post.first_message.id

    # Count existing comment-level divs
    initial_count = self.page.locator("[id^='comment-level-']").count()

    # Click the "Add comment" link
    add_link = self.page.locator(f"a[hx-get*='/comments'][hx-target='#create-comment-{first_message_id}']")
    add_link.click()
    self.page.wait_for_selector(f"#create-comment-{first_message_id} form.comment-form", timeout=2000)

    # Fill and submit
    self.page.locator(f"#create-comment-{first_message_id} input#id_comment_content").fill("A new HTMX comment from the test.")
    self.page.locator(f"#create-comment-{first_message_id} input[type='submit']").click()
    self.page.wait_for_timeout(1000)

    # The new comment should appear (as comment-level-{id}, not comment-div-{id})
    comment_levels = self.page.locator("[id^='comment-level-']")
    self.assertGreaterEqual(
      comment_levels.count(),
      initial_count + 1,
      "A new comment should appear after submitting the form",
    )

  def test_comment_display_shows_content(self):
    """The post detail should show the pre-existing comment content."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_selector(f"#comment-div-{self.comment.id}")

    comment_div = self.page.locator(f"#comment-div-{self.comment.id}").first
    self.assertTrue(comment_div.is_visible(), "Comment div should be visible")
    self.assertIn(
      self.comment.content,
      comment_div.inner_text(),
      "Comment content should be visible",
    )

  def test_edit_pre_existing_comment_via_htmx(self):
    """Editing the pre-existing comment (self.comment) via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_selector(f"#comment-div-{self.comment.id}")

    # Verify edit button is visible inside the comment div
    edit_btn = self.page.locator(f"#comment-div-{self.comment.id} button[hx-get$='/edit']")
    self.assertTrue(edit_btn.is_visible(), "Edit button should be visible for own comment")
    edit_btn.click()
    self.page.wait_for_selector(f"#edit-comment-{self.comment.id}", timeout=2000)

    # Edit the content
    self.page.locator(f"#edit-comment-{self.comment.id} input#id_comment_content").fill("Edited comment content.")
    self.page.locator(f"#edit-comment-{self.comment.id} button[type='submit']").click()
    self.page.wait_for_timeout(1000)

    # The display view should return
    display = self.page.locator(f"#comment-level-{self.comment.id}")
    self.assertTrue(display.is_visible(), "Comment display should be visible after edit")

  def test_delete_pre_existing_comment_via_htmx(self):
    """Deleting the pre-existing comment (self.comment) via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_selector(f"#comment-div-{self.comment.id}")

    # Verify delete button is visible
    delete_btn = self.page.locator(f"#comment-div-{self.comment.id} button[hx-post$='/delete']")
    self.assertTrue(delete_btn.is_visible(), "Delete button should be visible for own comment")

    # Handle confirm dialog
    self.page.on("dialog", lambda dialog: dialog.accept())
    delete_btn.click()

    # The comment div should be removed
    self.page.wait_for_selector(f"#comment-div-{self.comment.id}", state="detached", timeout=3000)
    self.assertEqual(
      self.page.locator(f"#comment-div-{self.comment.id}").count(),
      0,
      "Deleted comment should no longer be in the DOM",
    )
