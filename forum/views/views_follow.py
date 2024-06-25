from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

from ..models import Post


@login_required
def toggle_follow(request, pk):
  post = get_object_or_404(Post, pk=pk)
  if post.followers.filter(id=request.user.id).exists():
    post.followers.remove(request.user)
    messages.success(request, _("You are no longer following this post"))
  else:
    post.followers.add(request.user)
    messages.success(request, _("You are now following this post"))
    # send email to poster to tell him someone is following his post
    if post.first_message.author.id != request.user.id:  # don't send email to yourself
      post_url = request.build_absolute_uri(reverse("forum:display", args=[pk]))
      follower_name = request.user.get_full_name()
      post_title = post.title
      send_mail(
        _('New follower to your post "%(post_title)s"') % {'post_title': post_title},
        _('%(follower_name)s is now following your post "%(post_title)s"') %
        {'follower_name': follower_name, 'post_title': post_title},
        settings.DEFAULT_FROM_EMAIL,
        [post.first_message.author.email],
        html_message=render_to_string('forum/email/new_follower.html',
                                      {'post': post, 'follower': request.user,
                                       'post_url': post_url, 'site_name': settings.SITE_NAME}),
      )
  return redirect(reverse("forum:display", args=[pk]))


def check_followers_on_message(message):
  """sends an email to the followers of the post to which the message is added"""
  post = message.post
  # don't send email to the author of the message
  follower_emails = [follower.email for follower in post.followers.all() if follower.id != message.author.id]
  post_url = reverse("forum:display", args=[post.id])
  follower_name = message.author.get_full_name()
  post_title = post.title
  email = EmailMultiAlternatives(
    _('New reply to post "%(post_title)s"') % {'post_title': post_title},
    _('%(follower_name)s has posted a new message in the post "%(post_title)s"') %
    {'follower_name': follower_name, 'post_title': post_title},
    settings.DEFAULT_FROM_EMAIL,
    [],
    bcc=follower_emails,
  )
  html_message = render_to_string('forum/email/new_message_to_followers.html',
                                  {'post': post, 'message': message, 'post_url': post_url}
                                  )
  email.attach_alternative(html_message, "text/html")
  email.send()


def check_followers_on_comment(comment):
  """sends an email to followers of the post if the comment is a reply to a message of the post"""
  post = comment.message.post
  # don't send email to the author of the comment
  follower_emails = [follower.email for follower in post.followers.all() if follower.id != comment.author.id]
  post_url = reverse("forum:display", args=[post.id])
  follower_name = comment.author.get_full_name()
  post_title = post.title
  email = EmailMultiAlternatives(
    _('New comment on post "%(post_title)s"') % {'post_title': post_title},
    _('%(follower_name)s has added a new comment in the post "%(post_title)s"') %
    {'follower_name': follower_name, 'post_title': post_title},
    settings.DEFAULT_FROM_EMAIL,
    bcc=follower_emails,
  )
  html_message = render_to_string('forum/email/new_comment_to_followers.html',
                                  {'post': post, 'comment': comment, 'post_url': post_url}
                                  )
  email.attach_alternative(html_message, "text/html")
  email.send()
