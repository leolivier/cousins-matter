from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from ..services.members import do_toggle_follow

from ..models import Member


def toggle_follow(request, username):
  follower = request.user
  followed = get_object_or_404(Member, username=username)
  # use absolute URL for follower to avoid relative URLs in email
  follower_url = request.build_absolute_uri(reverse("members:detail", kwargs={"username": follower.username}))

  result, message = do_toggle_follow(followed, follower, follower_url)
  if result == "success":
    messages.success(request, message)
  else:
    messages.error(request, message)
  return redirect(reverse("members:detail", kwargs={"username": followed.username}))
