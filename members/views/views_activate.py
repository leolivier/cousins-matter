import logging

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _

from verify_email.email_handler import send_verification_email

from ..models import Member

logger = logging.getLogger(__name__)


def activate_member(request, username):
  """activate the member with username"""
  member = get_object_or_404(Member, username=username)
  if member.is_dead:
    messages.error(request, _("Error: Cannot activate a dead member"))
  elif member.is_active:
    if member.member_manager is not None:
      member.member_manager = None
      member.save()
    messages.error(request, _("Error: Member already active"))
  elif not member.email:
    messages.error(request, _("Error: Member without email cannot be activated"))
  else:
    send_verification_email(request, inactive_user=member)
    messages.success(
      request,
      _(
        "Member account successfully activated. The owner of the account will now receive an email "
        "containing an activation link then will be redirected to the password reset screen."
      ),
    )
    logger.info(f"Member {member.username} activated by {request.user.username}")

  return redirect(reverse("members:detail", kwargs={"username": member.username}))
