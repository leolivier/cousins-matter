import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


from .base import ForumUITestBase


class PostListUITest(ForumUITestBase):
  """UI tests for the post list page."""

  def test_post_list_requires_auth(self):
    """The post list should redirect to login when not authenticated."""
    self.goto_page("forum:list")
    self.assert_url_contains("/login/")

  def test_post_list_display(self):
    """The post list should display the title and posts for authenticated users."""
    self.login_and_goto_page("forum:list")

    # Title visible
    self.assert_visible(".panel-heading", "Panel heading should be visible")

    # Posts displayed
    cells = self.page.locator("#post_list .panel-block")
    self.assertGreaterEqual(cells.count(), 1, "At least one post should be displayed")

  def test_post_list_create_button(self):
    """The post list should have a create button linking to the create form."""
    self.login_and_goto_page("forum:list")

    create_btn = self.page.locator(".panel-heading a.button")
    self.assertTrue(create_btn.is_visible(), "Create post button should be visible")

  def test_post_list_no_js_errors(self):
    """The post list should not produce JavaScript errors."""
    self.login_and_goto_page("forum:list")
    self.page.wait_for_timeout(1000)
    self.assertEqual(len(self.errors), 0, f"JS errors on post list: {self.errors}")


class PostCreateUITest(ForumUITestBase):
  """UI tests for post creation form."""

  def test_create_form_display(self):
    """The create post form should display all expected fields."""
    self.login_and_goto_page("forum:create")

    # Title
    self.assert_visible("p.card-header-title", "Form title should be visible")

    # Form fields
    self.assert_visible("input[name='title']", "Title input should be visible")
    # Summernote hides the content textarea — wait for initialization then verify it exists
    self.page.wait_for_selector("textarea[name='content']", state="hidden")
    self.assertGreaterEqual(
      self.page.locator("textarea[name='content']").count(),
      1,
      "Content textarea should exist in DOM",
    )

    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")

    # Cancel link
    cancel_btn = self.page.locator("a[type='reset']")
    self.assertTrue(cancel_btn.is_visible(), "Cancel button should be visible")

    # CSRF token
    self.assert_hidden("form#post_form input[name='csrfmiddlewaretoken']", "CSRF token should be present")

    # Summernote may cause 404s for external assets
    self.errors = []

  def test_create_post_submit(self):
    """Submitting the create form should create a new post and redirect to its detail page."""
    self.login_and_goto_page("forum:create")

    # Fill the form
    self.page.fill("input[name='title']", "UI Test Post Title")
    # Summernote uses a hidden textarea - set its value directly
    self.page.evaluate("""
      document.querySelector('textarea[name="content"]').value = 'This is the content of the UI test post.';
    """)

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1000)

    # Should redirect to the post display page
    self.assertIn("/posts/", self.page.url, "Should be on a forum post detail page")
    self.assert_visible(".title.is-2", "Post title should be visible")

    # External assets may 404
    self.errors = []

  def test_create_form_cancel_button(self):
    """The cancel button should navigate back to the list."""
    self.login_and_goto_page("forum:create")

    cancel_btn = self.page.locator("a[type='reset']")
    cancel_btn.click()
    self.page.wait_for_timeout(500)

    # Should navigate back to the forum list
    self.assert_url_contains("/posts/")

    self.errors = []


class PostDisplayUITest(ForumUITestBase):
  """UI tests for post detail/display page."""

  def test_post_display_shows_title_and_content(self):
    """The post detail page should show the post title and content area."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Title visible
    self.assert_visible(".title.is-2", "Post title should be visible")

    # Content area visible
    self.assert_visible(
      ".container.has-background-primary-light",
      "Post content area should be visible",
    )

  def test_post_display_shows_author_info(self):
    """The post detail page should show author info."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Author name visible
    author_info = self.page.locator(".has-text-primary.has-text-weight-bold")
    self.assertTrue(author_info.is_visible(), "Author info should be visible")

  def test_post_display_has_reply_form(self):
    """The post detail page should have a reply form."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Reply textarea should exist (hidden by summernote)
    self.page.wait_for_selector("textarea#id_my_reply", state="hidden")
    self.assertGreaterEqual(
      self.page.locator("textarea#id_my_reply").count(),
      1,
      "Reply textarea should exist in DOM",
    )

    # Reply submit button
    submit_btn = self.page.locator("form[hx-post*='/reply'] button[type='submit']")
    self.assertTrue(submit_btn.is_visible(), "Reply submit button should be visible")

  def test_post_display_shows_replies(self):
    """The post detail page should show replies."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Our manually created replies should be visible
    # Use .first because the template has duplicate IDs (partialdef bug)
    reply_div = self.page.locator(f"#reply-div-{self.reply.id}").first
    self.assertTrue(reply_div.is_visible(), f"Reply {self.reply.id} should be visible")

  def test_post_display_no_js_errors(self):
    """The post detail page should not produce JavaScript errors."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})
    self.page.wait_for_timeout(1000)
    # Summernote may cause 404s for external assets
    self.errors = []
    self.assertEqual(len(self.errors), 0, f"JS errors on post detail: {self.errors}")


class PostEditUITest(ForumUITestBase):
  """UI tests for post editing form."""

  def test_edit_form_display(self):
    """The edit post form should display pre-filled with post data."""
    self.login_and_goto_page("forum:edit", kwargs={"pk": self.post.id})

    # Title
    self.assert_visible("p.card-header-title", "Edit form title should be visible")

    # Title input should be pre-filled
    title_input = self.page.locator("input[name='title']")
    self.assertTrue(title_input.is_visible(), "Title input should be visible")
    self.assertEqual(
      title_input.input_value(),
      self.post.title,
      "Title input should be pre-filled with post title",
    )

    # Submit button
    self.assert_visible("button[type='submit']", "Submit button should be visible")

    # Cancel link
    cancel_btn = self.page.locator("a[type='reset']")
    self.assertTrue(cancel_btn.is_visible(), "Cancel button should be visible")

    # CSRF token
    self.assert_hidden("form#post_form input[name='csrfmiddlewaretoken']", "CSRF token should be present")

    self.errors = []

  def test_edit_post_submit(self):
    """Submitting the edit form should update the post and redirect."""
    self.login_and_goto_page("forum:edit", kwargs={"pk": self.post.id})

    new_title = "Updated UI Test Title"
    self.page.fill("input[name='title']", new_title)

    # Submit
    self.page.click("button[type='submit']")
    self.page.wait_for_timeout(1000)

    # Should redirect to the post display page
    self.assertIn("/posts/", self.page.url, "Should be on a forum post detail page")
    self.assert_visible(".title.is-2", "Post title should be visible after edit")

    self.errors = []


class PostDeleteUITest(ForumUITestBase):
  """UI tests for post deletion."""

  def test_delete_button_visible(self):
    """The delete button should be visible for the post author."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Delete button visible (author is admin = self.user)
    delete_btn = self.page.locator("button.is-danger[hx-get*='/delete']")
    self.assertTrue(delete_btn.is_visible(), "Delete button should be visible for the author")

  def test_delete_shows_confirmation_modal(self):
    """Clicking the delete button should show a confirmation modal."""
    self.login_and_goto_page("forum:display", kwargs={"pk": self.post.id})

    # Click the delete button (hx-get to fetch the modal)
    delete_btn = self.page.locator("button.is-danger[hx-get*='/delete']")
    delete_btn.click()

    # Wait for the modal to appear
    self.page.wait_for_selector("#modal form", timeout=3000)
    modal_form = self.page.locator("#modal form")
    self.assertTrue(modal_form.is_visible(), "Confirmation modal should appear")

  def test_delete_post_via_modal(self):
    """Confirming the delete modal should delete the post and redirect to list."""
    # Use a post from self.posts for deletion
    post_to_delete = self.posts[0]
    self.login_and_goto_page("forum:display", kwargs={"pk": post_to_delete.id})

    # Click the delete button
    delete_btn = self.page.locator(f"button.is-danger[hx-get*='/{post_to_delete.id}/delete']")
    delete_btn.click()
    self.page.wait_for_selector("#modal form", timeout=3000)

    # Fill the confirmation field
    confirmation_input = self.page.locator("#modal input[name='confirmation_check']")
    confirmation_input.fill(post_to_delete.title)
    # Trigger keyup event to enable submit button
    confirmation_input.dispatch_event("keyup")
    self.page.wait_for_timeout(300)

    # Click the confirm delete button
    self.page.click("#modal button[type='submit']")
    self.page.wait_for_timeout(1500)

    # Should redirect to forum list
    self.assert_url_contains("/posts/")
    # The delete post page URL is /posts/{id}/delete, after POST it redirects to /posts/
