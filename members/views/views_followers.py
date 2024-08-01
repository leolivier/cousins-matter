from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail

from ..models import Member


@login_required
def toggle_follow(request, pk):
  follower = request.user
  followed = get_object_or_404(Member, pk=pk)
  followed_url = reverse('members:detail', args=[pk])
  followed_name = followed.full_name

  if followed == follower:
    messages.error(request, _("You can't follow yourself!"))
  elif followed.followers.filter(id=follower.id).exists():
    followed.followers.remove(follower)
    messages.success(request, _("You are no longer following %(followed_name)s") % {'followed_name': followed_name})
  else:
    followed.followers.add(follower)
    messages.success(request, _("You are now following %(followed_name)s") % {'followed_name': followed_name})
    # send email to followed to tell him/her someone is following him/her
    followed_url = followed_url
    follower_name = follower.full_name
    title = _('You have a new follower!')
    message = _('%(follower_name)s is now following you!') % {'follower_name': follower_name}
    follower_url = request.build_absolute_uri(reverse('members:detail', args=[follower.id]))

    send_mail(
      title,
      message,
      settings.DEFAULT_FROM_EMAIL,
      [followed.email],
      html_message=render_to_string('members/email/new_follower.html', {
        'title': title,
        'follower_name': follower_name,
        'followed_name': followed_name,
        'follower_url': follower_url,
        'site_name': settings.SITE_NAME}),
    )
  return redirect(followed_url)
