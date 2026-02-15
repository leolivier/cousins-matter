from django.shortcuts import get_object_or_404
from django.urls import reverse

from cm_main import followers
from ..models import Post


def post_url(post_id):
  return reverse("forum:display", args=[post_id])


def toggle_follow(request, pk):
  post = get_object_or_404(Post, pk=pk)
  return followers.toggle_follow(request, post, post.first_message.author, post_url(pk))


def check_followers_on_new_post(request, post):
  """sends an email to the followers of the post to which the message is added"""
  followers.check_followers(request, post, request.user, post_url(post.id))


def check_followers_on_message(request, message):
  """sends an email to the followers of the post to which the message is added"""
  post = message.post
  followers.check_followers(request, post, post.owner, post_url(post.id), message, message.author)


def check_followers_on_comment(request, comment):
  """sends an email to followers of the post if the comment is a reply to a message of the post"""
  post = comment.message.post
  followers.check_followers(request, post, post.owner, post_url(post.id), comment, comment.author)
