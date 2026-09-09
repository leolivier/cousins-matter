"""Query-count regression tests: page renders must not scale with the number of objects."""

from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from ..models import Message, Post
from .tests_post import ForumTestCase


class PostsListQueryCountTestCase(ForumTestCase):
  def _render_list(self):
    with CaptureQueriesContext(connection) as ctx:
      response = self.client.get(reverse("forum:list"))
    self.assertEqual(response.status_code, 200)
    return len(ctx)

  def test_post_list_queries_do_not_scale_with_posts(self):
    """The list page must issue the same number of queries for 1 and 5 posts: follower
    count and follow-state come from the precomputed num_followers/is_following annotations,
    not from per-post queries in the followers template tags."""
    self._render_list()  # warm-up: the very first request populates per-process caches
    with_1_post = self._render_list()
    with transaction.atomic():
      for i in range(4):
        message = Message(content=f"message {i}", author=self.member)
        message.save()
        post = Post(title=f"title {i}", first_message=message)
        post.save()
        message.post = post
        message.save()
    self.assertEqual(self._render_list(), with_1_post)
