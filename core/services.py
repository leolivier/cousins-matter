import asyncio
import io
import logging
import os
from typing import Any
from uuid import uuid4

import redis
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, connections
from django.db.migrations.exceptions import InconsistentMigrationHistory
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django_q.tasks import async_task, result

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
    # the connection error text (host/port, no credentials) helps the env-check page
    return {"status": "redis_error", "msg": f"redis error: {e}"}
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
        {"key": _("This site is managed by"), "value": admin.full_name if admin else _("(no admin yet)")},
        {"key": _("Administrator email"), "value": admin.email if admin else ""},
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


# --------------------------------------------------------------------------------------
# environment checks (superuser diagnostics page, core:env_check)
# --------------------------------------------------------------------------------------


def _line(name: str, status: str, detail: str, long_output: bool = False) -> dict[str, Any]:
  """Builds one check row for the env_check page (status: ok|warning|error|skipped)."""
  return {"name": name, "status": status, "label": _(status), "detail": detail, "long_output": long_output}


def _probe_db_and_redis() -> list[dict[str, Any]]:
  check = health_check()
  if check["status"] == "db_error":
    return [
      _line(_("Database"), "error", check["msg"]),
      _line(_("Redis"), "skipped", _("Not checked (database unreachable)")),
    ]
  if check["status"] == "redis_error":
    return [
      _line(_("Database"), "ok", _("SELECT 1 succeeded")),
      _line(_("Redis"), "error", check["msg"]),
    ]
  return [
    _line(_("Database"), "ok", _("SELECT 1 succeeded")),
    _line(_("Redis"), "ok", _("PING succeeded")),
  ]


def _probe_django_q() -> list[dict[str, Any]]:
  # the queue needs its broker (redis): skip with a clear reason when a dependency is down
  infra = health_check()
  if infra["status"] == "redis_error":
    return [_line(_("Django-Q2 task queue"), "skipped", _("Skipped: Redis is unreachable"))]
  if infra["status"] == "db_error":
    return [_line(_("Django-Q2 task queue"), "skipped", _("Skipped: Database is unreachable"))]
  task_id = async_task("core.services.health_check")
  check = result(task_id, 1000)
  if check and isinstance(check, dict) and check.get("status") == "ok":
    if settings.Q_CLUSTER.get("sync"):
      # the task ran in-process: it proves nothing about a live qcluster worker
      return [_line(_("Django-Q2 task queue"), "ok", _("Task roundtrip succeeded (sync mode: executed in-process)"))]
    return [_line(_("Django-Q2 task queue"), "ok", _("Task roundtrip through the worker succeeded"))]
  return [_line(_("Django-Q2 task queue"), "warning", _("No task result within 1s: is the qcluster worker running?"))]


def _probe_migrations() -> list[dict[str, Any]]:
  buf = io.StringIO()
  try:
    call_command("migrate", "--check", stdout=buf, stderr=buf)
  except (CommandError, DatabaseError, LookupError, InconsistentMigrationHistory, SystemExit) as e:
    # --check exits through sys.exit(1) when migrations are unapplied;
    # LookupError covers NodeNotFoundError (broken migration graph)
    detail = buf.getvalue().strip() or str(e) or _("Unapplied migrations")
    return [_line(_("Migrations"), "warning", detail)]
  return [_line(_("Migrations"), "ok", _("All migrations applied"))]


def _probe_deploy_check() -> list[dict[str, Any]]:
  buf = io.StringIO()
  try:
    call_command("check", deploy=True, stdout=buf, stderr=buf)
  except CommandError as e:
    output = f"{buf.getvalue().strip()}\n{e}".strip()
    return [_line(_("Deployment checks"), "warning", output, long_output=True)]
  output = buf.getvalue().strip()
  if output:
    return [_line(_("Deployment checks"), "warning", output, long_output=True)]
  return [_line(_("Deployment checks"), "ok", _("No deployment issue found"))]


def _probe_media() -> list[dict[str, Any]]:
  storage = storages["default"]
  backend = f"{type(storage).__module__}.{type(storage).__name__}"
  path = f"env_check/{uuid4().hex}.txt"
  storage.save(path, ContentFile(b"ok"))
  try:
    with storage.open(path) as f:
      content = f.read()
  finally:
    storage.delete(path)
  if content != b"ok":
    return [_line(_("Media storage"), "error", _("Read-back mismatch on %(backend)s") % {"backend": backend})]
  return [_line(_("Media storage"), "ok", _("Write/read/delete roundtrip succeeded on %(backend)s") % {"backend": backend})]


async def _channels_roundtrip(layer) -> Any:
  channel = await layer.new_channel()
  await layer.send(channel, {"type": "env.check.ping"})
  # channels-redis receive() has no timeout parameter: use asyncio.wait_for
  return await asyncio.wait_for(layer.receive(channel), 5)


def _probe_channels() -> list[dict[str, Any]]:
  layer = get_channel_layer()
  if layer is None:
    return [_line(_("Chat (Channels)"), "error", _("No channel layer configured"))]
  try:
    asyncio.run(_channels_roundtrip(layer))
  except TimeoutError:
    return [_line(_("Chat (Channels)"), "warning", _("No message echoed back within 5s"))]
  return [
    _line(_("Chat (Channels)"), "ok", _("Roundtrip succeeded on channel layer %(layer)s") % {"layer": type(layer).__name__})
  ]


def _probe_tenants() -> list[dict[str, Any]]:
  from tenants.models import Tenant
  from tenants.scoping import get_current_tenant

  if not settings.MULTI_TENANT_ENABLED:
    return [_line(_("Multi-tenancy"), "skipped", _("Multi-tenancy is disabled"))]
  try:
    Tenant.get_default()
  except Tenant.DoesNotExist:
    return [
      _line(
        _("Multi-tenancy"),
        "error",
        _("Missing tenant with slug '%(slug)s' (DEFAULT_TENANT_SLUG)") % {"slug": settings.DEFAULT_TENANT_SLUG},
      )
    ]
  try:
    Tenant.get_system()
  except Tenant.DoesNotExist:
    return [
      _line(
        _("Multi-tenancy"),
        "error",
        _("Missing tenant with slug '%(slug)s' (SYSTEM_TENANT_SLUG)") % {"slug": settings.SYSTEM_TENANT_SLUG},
      )
    ]
  current = get_current_tenant()
  return [
    _line(
      _("Multi-tenancy"),
      "ok",
      _("%(count)d tenant(s), current: %(current)s")
      % {"count": Tenant.objects.count(), "current": current.slug if current else _("none")},
    )
  ]


def _probe_email() -> list[dict[str, Any]]:
  backend = settings.EMAIL_BACKEND
  if "console" in backend or "locmem" in backend:
    return [_line(_("Email"), "warning", _("Development backend %(backend)s: no real email is sent") % {"backend": backend})]
  return [_line(_("Email"), "ok", backend)]


def run_env_checks() -> list[dict[str, Any]]:
  """
  Runs every environment probe and returns the rows for the env_check page.

  Each probe is individually wrapped in try/except: a failing probe yields an
  "error" row, never an exception - the diagnostics page must always render.
  """
  probes = [
    (_("Database & Redis"), _probe_db_and_redis),
    (_("Django-Q2 task queue"), _probe_django_q),
    (_("Migrations"), _probe_migrations),
    (_("Deployment checks"), _probe_deploy_check),
    (_("Media storage"), _probe_media),
    (_("Chat (Channels)"), _probe_channels),
    (_("Multi-tenancy"), _probe_tenants),
    (_("Email"), _probe_email),
  ]
  results: list[dict[str, Any]] = []
  for name, probe in probes:
    try:
      results.extend(probe())
    except Exception as e:
      logger.exception("Environment check probe '%s' failed", name)
      results.append(_line(name, "error", str(e)))
  return results


def send_test_email(user) -> tuple[bool, str]:
  """Sends a test email to the given (super)user; returns (success, detail)."""
  if not user.email:
    return False, _("User %(username)s has no email address") % {"username": user.username}
  try:
    send_mail(
      subject=_("Cousins Matter - environment check"),
      message=_("Congratulations! Your email backend works. This test email was sent from the environment check page."),
      from_email=settings.DEFAULT_FROM_EMAIL,
      recipient_list=[user.email],
      fail_silently=False,
    )
  except Exception as e:
    logger.exception("Test email to %s failed", user.email)
    return False, str(e)
  return True, _("Test email sent to %s") % user.email
