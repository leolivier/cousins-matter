import os

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from core.tests.ui import PlaywrightTestCase
from forum.tests.factories import CommentFactory, MessageFactory, PostFactory


class ForumUITestBase(PlaywrightTestCase):
  """Base class for Forum UI tests with pre-created test fixtures."""

  def setUp(self):
    super().setUp()

    # Create posts without auto-thread for list page tests (fast, predictable)
    self.posts = PostFactory.create_batch(
      12,
      first_message__author=self.user,
      create_thread=False,
    )

    # Create one post for detail page tests
    self.post = PostFactory(
      title="Test Post for Detail Page",
      first_message__author=self.user,
      create_thread=False,
    )

    # Add replies to the detail post (one by admin, one to keep it simple)
    self.reply = MessageFactory(
      post=self.post,
      author=self.user,
      content="This is a reply from the admin user.",
    )

    # Another reply from the same user for edit/delete tests
    self.reply2 = MessageFactory(
      post=self.post,
      author=self.user,
      content="Second reply from admin for testing.",
    )

    # Add a comment on the post's first message
    self.comment = CommentFactory(
      message=self.post.first_message,
      author=self.user,
      content="Admin's comment on the first message.",
    )
