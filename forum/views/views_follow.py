from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from cm_main import followers
from ..models import Post


@login_required
def toggle_follow(request, pk):
  post = get_object_or_404(Post, pk=pk)
  return followers.toggle_follow(request, post, post.first_message.author,
                                 reverse("forum:display", args=[pk]))


def check_followers_on_message(request, message):
  """sends an email to the followers of the post to which the message is added"""
  followers.check_followers(request, message.post, {'message': message}, message.author,
                            reverse("forum:display", args=[message.post.id]))


def check_followers_on_comment(request, comment):
  """sends an email to followers of the post if the comment is a reply to a message of the post"""
  followers.check_followers(request, comment.message.post, {'comment': comment}, comment.author,
                            reverse("forum:display", args=[comment.message.post.id]))
