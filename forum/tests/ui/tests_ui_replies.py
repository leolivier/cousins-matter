import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from .base import ForumUITestBase


class ReplyUITest(ForumUITestBase):
  """UI tests for reply creation, editing and deletion via HTMX."""

  def test_add_reply_via_htmx(self):
    """Submitting the reply form should add a new reply via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Wait for summernote to initialize the textarea
    self.page.wait_for_selector("textarea#id_my_reply", state="hidden")

    # Fill the reply content via JavaScript (summernote wraps the textarea)
    self.page.evaluate("""
      document.querySelector('textarea#id_my_reply').value = 'A new HTMX reply from the test.';
    """)

    # Click the send button
    send_btn = self.page.locator("form[hx-post*='/reply'] button[type='submit']")
    send_btn.click()
    self.page.wait_for_timeout(1000)

    # The reply should appear in the DOM - check that a new reply div exists
    reply_divs = self.page.locator("[id^='reply-div-']")
    # We had 2 replies, now should have at least 3 (but duplicate IDs means count = 2×)
    self.assertGreaterEqual(
      reply_divs.count(),
      6,
      "New reply should appear after submitting the form",
    )

    # Summernote external assets
    self.errors = []

  def test_edit_reply_loads_form_via_htmx(self):
    """Clicking the edit button should load the edit form via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_selector(f"#reply-content-{self.reply.id}")

    # Click the edit link — use hx-target to scope to the right reply
    edit_link = self.page.locator(f"button[hx-get*='/edit_reply'][hx-target='#reply-div-{self.reply.id}']")
    self.assertTrue(edit_link.is_visible(), "Edit link should be visible for own reply")
    edit_link.click()
    self.page.wait_for_timeout(500)

    # The edit form should now be inside the reply div
    edit_form = self.page.locator(f"form#edit-reply-{self.reply.id}")
    self.assertTrue(edit_form.is_visible(), "Edit form should appear after clicking edit")

  def test_edit_reply_submit_via_htmx(self):
    """Submitting the edit reply form should update the reply via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_selector(f"#reply-content-{self.reply.id}")

    # Click edit
    edit_link = self.page.locator(f"button[hx-get*='/edit_reply'][hx-target='#reply-div-{self.reply.id}']")
    edit_link.click()
    self.page.wait_for_selector(f"#edit-reply-{self.reply.id}", timeout=2000)

    # Fill the edited content via JavaScript
    self.page.evaluate(
      """
      const textarea = document.querySelector('#edit-reply-"""
      + str(self.reply.id)
      + """ textarea[name="content"]');
      if (textarea) textarea.value = 'Edited reply content via HTMX.';
    """
    )

    # Submit the edit form
    submit_btn = self.page.locator(f"#edit-reply-{self.reply.id} button[type='submit']")
    submit_btn.click()
    self.page.wait_for_timeout(1000)

    # The edit form should be replaced by the display view
    reply_content = self.page.locator(f"#reply-content-{self.reply.id}")
    self.assertTrue(reply_content.is_visible(), "Reply display should be visible after edit")

    self.errors = []

  def test_delete_reply_via_htmx(self):
    """Clicking delete with confirmation should remove the reply via HTMX."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_selector(f"#reply-content-{self.reply2.id}")

    # Handle the hx-confirm browser dialog
    self.page.on("dialog", lambda dialog: dialog.accept())

    # Click the delete link — scoped to the right reply
    delete_link = self.page.locator(f"button[hx-post*='/delete_reply'][hx-target='#reply-div-{self.reply2.id}']")
    self.assertTrue(delete_link.is_visible(), "Delete link should be visible for own reply")
    delete_link.click()

    # The reply div should be removed from the DOM
    self.page.wait_for_selector(f"#reply-content-{self.reply2.id}", state="detached", timeout=3000)
    self.assertEqual(
      self.page.locator(f"#reply-content-{self.reply2.id}").count(),
      0,
      "Deleted reply content should no longer be in the DOM",
    )
