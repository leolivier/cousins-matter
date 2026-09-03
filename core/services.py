import logging
import os

import redis
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.mail import EmailMultiAlternatives
from django.db import DatabaseError, connections
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from chat.models import ChatMessage, ChatRoom, PrivateChatRoom
from forum.models import Comment, Message, Post
from galleries.models import Gallery, Photo
from members.models import Member

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------------
# infrastructure health
# --------------------------------------------------------------------------------------

redis_client = redis.Redis(
  host=os.getenv("REDIS_HOST", "redis"),
  port=int(os.getenv("REDIS_PORT", "6379")),
  decode_responses=True,
)


def health_check() -> dict[str, str]:
  try:
    with connections["default"].cursor() as cursor:
      cursor.execute("SELECT 1")
      cursor.fetchone()
  except DatabaseError as e:
    logger.error(f"Database error: {e}")
    return {"status": "db_error", "msg": "database error, see logs"}
  try:
    redis_client.ping()
  except redis.exceptions.ConnectionError as e:
    logger.error(f"Redis error: {e}")
    return {"status": "redis_error", "msg": "redis error, see logs"}
  return {"status": "ok"}


# --------------------------------------------------------------------------------------
# site statistics
# --------------------------------------------------------------------------------------


def build_site_stats(site_url: str, release_text: dict) -> dict:
  """
  Builds the site-stats context for ``core/about/site-stats.html``: object counts across the
  apps and the site administrator.

  ``release_text`` (the latest-release descriptor) and ``site_url`` are fetched by the caller
  in the view, since they need the HTTP request (the version lookup reports errors through the
  messages framework, and the URL comes from ``request.build_absolute_uri``).
  """
  from tenants.authz import admin_or_superusers
  from tenants.scoping import get_current_tenant
  _admins = admin_or_superusers(get_current_tenant())
  admin = _admins[0] if _admins else None
  all_messages_count = ChatMessage.objects.count()
  public_chat_rooms = ChatRoom.objects.public()
  public_chat_messages_count = ChatMessage.objects.filter(room__in=public_chat_rooms).count()

  return {
    "site": {
      "key": _("Site"),
      "stats": [
        {"key": _("Site name"), "value": settings.SITE_NAME},
        {"key": _("Site URL"), "value": site_url},
        {"key": _("Application Version"), "value": settings.APP_VERSION},
        {"key": _("Latest release"), "value": release_text},
      ],
    },
    "members": {
      "key": _("Members"),
      "stats": [
        {"key": _("Total number of members"), "value": Member.objects.count()},
        {
          "key": _("Number of active members"),
          "value": Member.objects.filter(is_active=True).count(),
        },
        {
          "key": _("Number of managed members"),
          "value": Member.objects.filter(is_active=False).count(),
        },
      ],
    },
    "galleries": {
      "key": _("Galleries"),
      "stats": [
        {"key": _("Number of galleries"), "value": Gallery.objects.count()},
        {"key": _("Number of photos"), "value": Photo.objects.count()},
      ],
    },
    "forums": {
      "key": _("Forums"),
      "stats": [
        {"key": _("Number of posts"), "value": Post.objects.count()},
        {"key": _("Number of post messages"), "value": Message.objects.count()},
        {
          "key": _("Number of message comments"),
          "value": Comment.objects.count(),
        },
      ],
    },
    "chats": {
      "key": _("Chats"),
      "stats": [
        {"key": _("Number of chat rooms"), "value": ChatRoom.objects.count()},
        {
          "key": _("Number of public chat rooms"),
          "value": ChatRoom.objects.public().count(),
        },
        {
          "key": _("Number of private chat rooms"),
          "value": PrivateChatRoom.objects.count(),
        },
        {"key": _("Number of chat messages"), "value": all_messages_count},
        {
          "key": _("Number of private chat messages"),
          "value": all_messages_count - public_chat_messages_count,
        },
        {
          "key": _("Number of public chat messages"),
          "value": public_chat_messages_count,
        },
      ],
    },
    "admin": {
      "key": _("Administrator"),
      "stats": [
        {"key": _("This site is managed by"), "value": admin.full_name},
        {"key": _("Administrator email"), "value": admin.email},
      ],
    },
  }


# --------------------------------------------------------------------------------------
# contact form
# --------------------------------------------------------------------------------------


def do_send_contact_email(sender, recipient, message, attachment=None):
  """
  Builds and sends the contact-form email from ``sender`` to ``recipient`` (the site admin).

  ``attachment`` is an uploaded file (``InMemoryUploadedFile`` / ``TemporaryUploadedFile``) or
  ``None``; any other type raises ``ValueError`` (preserved from the original view behaviour).
  """
  title = _("You have a new message from %(name)s (%(email)s). ") % {
    "name": sender.full_name,
    "email": sender.email,
  }
  email = EmailMultiAlternatives(
    subject=_("Contact form"),
    body=title + _("But your mailer tools is too old to show it :'("),
    from_email=settings.DEFAULT_FROM_EMAIL,
    to=[recipient.email],
    reply_to=[sender.email],
  )
  # attach an HTML version of the message
  html_message = render_to_string(
    "core/contact/email-contact-form.html",
    {
      "title": title,
      "sender": sender,
      "message": message,
      "site_name": settings.SITE_NAME,
    },
  )
  email.attach_alternative(html_message, "text/html")

  # attach the uploaded file if any
  if attachment is not None:
    if isinstance(attachment, (InMemoryUploadedFile, TemporaryUploadedFile)):
      email.attach(
        attachment.name,
        attachment.read(),
        attachment.content_type,
      )
    else:
      raise ValueError(_("This file type is not supported"))

  # and send the email
  email.send(fail_silently=False)
