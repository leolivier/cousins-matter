"""Transactional e-mail helper: queue on the Django-Q cluster, never block the request.

A slow or unreachable SMTP server must not slow down (or fail) a signup, an
upload or a Stripe webhook. ``send_mail_async`` hands the message to the
``qcluster`` process, which retries it like any other task. Development and
tests keep ``Q_CLUSTER["sync"] = True`` and therefore send inline, exactly as
before.

Only plain data crosses the queue: subjects and bodies are rendered to
``str`` first, so lazy translation objects are resolved in the caller's
language instead of whatever language the worker happens to have loaded.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django_q.tasks import async_task

logger = logging.getLogger(__name__)

# Mail is quick compared to imports; a shorter timeout lets a stuck SMTP
# connection fail (and retry) without occupying a worker for a full minute.
MAIL_TASK_TIMEOUT = 30


def send_mail_async(
  subject,
  message: str,
  from_email: str | None = None,
  recipient_list=(),
  html_message: str | None = None,
):
  """Send ``send_mail`` through qcluster; fall back to a synchronous send.

  Returns the task id when queued, or the number of sent messages when the
  e-mail is sent inline (sync mode or queue unavailable).
  """
  subject = str(subject)
  message = str(message)
  if html_message is not None:
    html_message = str(html_message)
  from_email = from_email or settings.DEFAULT_FROM_EMAIL
  recipients = list(recipient_list)
  if settings.Q_CLUSTER.get("sync", False):
    return send_mail(subject, message, from_email, recipients, html_message=html_message)
  try:
    return async_task(
      "django.core.mail.send_mail",
      subject,
      message,
      from_email,
      recipients,
      html_message=html_message,
      q_options={"timeout": MAIL_TASK_TIMEOUT},
    )
  except Exception:  # broker down: better a blocking send than a lost e-mail
    logger.exception("Could not queue an e-mail; sending it synchronously")
    return send_mail(subject, message, from_email, recipients, html_message=html_message)


def send_multi_alternatives(
  subject,
  body: str,
  recipient_list=(),
  bcc=(),
  html_message: str | None = None,
  from_email: str | None = None,
) -> int:
  """Send one e-mail to many recipients (optionally BCC), plain + HTML."""
  message = EmailMultiAlternatives(
    str(subject),
    str(body),
    from_email or settings.DEFAULT_FROM_EMAIL,
    list(recipient_list),
    bcc=list(bcc),
  )
  if html_message:
    message.attach_alternative(str(html_message), "text/html")
  return message.send()


def send_multi_alternatives_async(
  subject,
  body: str,
  recipient_list=(),
  bcc=(),
  html_message: str | None = None,
  from_email: str | None = None,
):
  """Queue :func:`send_multi_alternatives` on qcluster (sync in dev/tests)."""
  subject = str(subject)
  body = str(body)
  if settings.Q_CLUSTER.get("sync", False):
    return send_multi_alternatives(subject, body, recipient_list, bcc, html_message, from_email)
  try:
    return async_task(
      "core.mailer.send_multi_alternatives",
      subject,
      body,
      list(recipient_list),
      list(bcc),
      html_message=html_message,
      from_email=from_email,
      q_options={"timeout": MAIL_TASK_TIMEOUT},
    )
  except Exception:  # broker down: better a blocking send than a lost e-mail
    logger.exception("Could not queue an e-mail; sending it synchronously")
    return send_multi_alternatives(subject, body, recipient_list, bcc, html_message, from_email)
