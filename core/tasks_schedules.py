import sys
import json
import logging
from django_q.models import Schedule

logger = logging.getLogger(__name__)


def setup_notification_schedules():
  """
  Initializes summary email notification schedules if not already present.
  """
  # Do not run if we are migrating or testing or during one-off commands
  if any(arg in sys.argv for arg in ["makemigrations", "migrate", "test", "collectstatic"]):
    return

  try:
    _setup_schedule("hourly", "Hourly Notifications", Schedule.HOURLY)
    _setup_schedule("daily", "Daily Notifications", Schedule.DAILY)
    _setup_schedule("weekly", "Weekly Notifications", Schedule.WEEKLY)

    # Check if MONTHLY exists, otherwise use CRON
    schedule_type = getattr(Schedule, "MONTHLY", None)
    if schedule_type:
      _setup_schedule("monthly", "Monthly Notifications", schedule_type)
    else:
      # Cron for 1st of month at 00:00: "0 0 1 * *"
      Schedule.objects.get_or_create(
        name="Monthly Notifications",
        defaults={
          "func": "core.tasks.process_batched_notifications",
          "args": json.dumps("monthly"),
          "schedule_type": Schedule.CRON,
          "cron": "0 0 1 * *",
          "repeats": -1,
        },
      )
      _repair_args("Monthly Notifications", "monthly")
  except Exception as e:
    # This can happen if the database is not ready or migrations haven't run
    logger.debug(f"Could not setup schedules: {e}")


def _setup_schedule(frequency, name, schedule_type):
  """
  Sets up a single schedule.
  """
  # We use get_or_create to avoid duplicates.
  # We only update if it doesn't exist to allow manual changes in admin.
  Schedule.objects.get_or_create(
    name=name,
    defaults={
      "func": "core.tasks.process_batched_notifications",
      # django-q2 parses Schedule.args with ast.literal_eval on every tick:
      # it must be a Python literal (quoted string), not a bare word
      "args": json.dumps(frequency),
      "schedule_type": schedule_type,
      "repeats": -1,  # Forever
    },
  )
  _repair_args(name, frequency)


def _repair_args(name, frequency):
  """Fix schedules created before args were stored as literals.

  Bare-word args ("hourly") made django-q2's scheduler fail with
  "malformed node or string" and the notifications never ran. Only exact
  bare-word matches are repaired, manual admin edits are left alone.
  """
  Schedule.objects.filter(name=name, args=frequency).update(args=json.dumps(frequency))
