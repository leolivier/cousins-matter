import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from .models import NotificationEvent

logger = logging.getLogger(__name__)


def process_batched_notifications(frequency):
  """
  Processes batched notifications for a given frequency.
  """
  logger.info(f"Processing batched notifications for frequency: {frequency}")

  # Get all pending events for members with this frequency
  events = NotificationEvent.objects.filter(member__email_batch_frequency=frequency).select_related("member", "author")

  if not events.exists():
    logger.debug(f"No pending events for frequency: {frequency}")
    return

  # Group by member
  member_events = {}
  for event in events:
    if event.member not in member_events:
      member_events[event.member] = []
    member_events[event.member].append(event)

  for member, evs in member_events.items():
    if not member.email:
      logger.warning(f"Member {member.username} has no email, skipping notifications.")
      NotificationEvent.objects.filter(id__in=[ev.id for ev in evs]).delete()
      continue

    # Aggregate notifications
    notifications_data = []
    for ev in evs:
      # Check if objects still exist (GenericForeignKey returns None if object is deleted)
      if ev.followed_object is None:
        continue

      followed_obj = ev.followed_object
      new_obj = ev.new_object

      followed_object_name = str(followed_obj)
      followed_type = followed_obj._meta.verbose_name
      obj_type = new_obj._meta.verbose_name if new_obj else followed_type
      obj_str = str(new_obj) if new_obj else followed_object_name

      author_name = ev.author.full_name if ev.author else _("Unknown")
      is_creation = (followed_obj == new_obj) or (new_obj is None)

      notifications_data.append({
        "author_name": author_name,
        "is_creation": is_creation,
        "followed_type": followed_type,
        "followed_object_name": followed_object_name,
        "obj_type": obj_type,
        "obj_str": obj_str,
        "url": ev.followed_object_url,
        "created_at": ev.created_at,
      })

    if not notifications_data:
      logger.debug(f"No valid notifications left for member {member.username} after filtering deleted objects.")
      NotificationEvent.objects.filter(id__in=[ev.id for ev in evs]).delete()
      continue

    # Send summary email
    # frequency is the internal value (hourly, daily, etc.)
    # Let's map it to a nice display name
    from members.models import Member

    frequency_display = dict(Member.FREQUENCY_CHOICES).get(frequency, frequency)
    title = _('Summary of notifications (%(frequency)s) for "%(site_name)s"') % {
      "frequency": frequency_display,
      "site_name": settings.SITE_NAME,
    }

    context = {
      "member": member,
      "notifications": notifications_data,
      "frequency_display": frequency_display,
      "title": title,
      "site_name": settings.SITE_NAME,
    }

    html_message = render_to_string("core/followers/email-notification-summary.html", context)
    # Plain text summary
    body = _("You have %(count)s new notifications.") % {"count": len(notifications_data)}

    email = EmailMultiAlternatives(
      title,
      body,
      settings.DEFAULT_FROM_EMAIL,
      [member.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send()

    # Delete processed events for this member
    ids = [ev.id for ev in evs]
    NotificationEvent.objects.filter(id__in=ids).delete()
    logger.info(f"Sent summary email to {member.email} with {len(notifications_data)} notifications.")
