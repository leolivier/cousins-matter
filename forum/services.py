import logging

from django.db import transaction
from django.db.models import Count, Prefetch

from .models import Comment, Message, Post

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------------
# post listing / display
# --------------------------------------------------------------------------------------


def get_posts_list_queryset():
  """
  Queryset of posts for the list view: each annotated with its message and follower counts,
  the first message's author prefetched, most recent first.

  ``distinct=True`` is required on both counts: annotating two aggregates (messages +
  followers) in one queryset cross-joins them and would multiply both counts otherwise.
  """
  return (
    Post.objects
    .select_related("first_message__author")
    .annotate(num_messages=Count("message", distinct=True), num_followers=Count("followers", distinct=True))
    .order_by("-first_message__created")
  )


def get_post_replies_queryset(post):
  """Ordered replies of ``post`` (excluding its first message), with author and comments prefetched for rendering."""
  return (
    Message.objects
    .filter(post=post, first_of_post=None)
    .select_related("author")
    .prefetch_related(Prefetch("comment_set", queryset=Comment.objects.select_related("author")))
  )


# --------------------------------------------------------------------------------------
# post creation
# --------------------------------------------------------------------------------------


def do_create_post(author, post_form, message_form):
  """
  Creates a post and its first message atomically from two *validated* model forms.

  Returns ``(post, message)``. Notifying the author's followers is left to the caller (it
  needs the HTTP request). On failure inside ``transaction.atomic()`` the saves roll back;
  the caller owns any cleanup if a post-transaction step (e.g. follower notification) raises.
  """
  message_form.instance.author_id = author.id
  with transaction.atomic():
    message = message_form.save()
    post_form.instance.first_message = message
    post = post_form.save()
    message.post = post
    message.save()
  return post, message
