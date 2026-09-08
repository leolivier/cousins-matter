"""Notification schedules must be parseable by django-q2's scheduler.

django-q2 runs `ast.literal_eval(Schedule.args)` on every tick: args stored
as bare words ("hourly") make it log "Could not create task from schedule"
and the notification emails never fire.
"""

import ast
from unittest import mock

from django_q.models import Schedule
from django.test import TestCase

from core.tasks_schedules import _setup_schedule, setup_notification_schedules


def _literal_ok(args) -> bool:
  try:
    ast.literal_eval(args)
    return True
  except (ValueError, SyntaxError):
    return False


class NotificationSchedulesTests(TestCase):
  def test_created_schedule_args_are_python_literals(self):
    _setup_schedule("hourly", "Test Hourly Notifications", Schedule.HOURLY)
    schedule = Schedule.objects.get(name="Test Hourly Notifications")
    self.assertTrue(_literal_ok(schedule.args), f"malformed args: {schedule.args!r}")
    # and it round-trips to the frequency string the task expects
    parsed = ast.literal_eval(schedule.args)
    self.assertEqual(parsed if isinstance(parsed, str) else parsed[0], "hourly")

  def test_all_setup_schedules_are_parseable(self):
    # bypass the argv guard (it skips when run under the test runner)
    with mock.patch("core.tasks_schedules.sys.argv", ["manage.py"]):
      setup_notification_schedules()
    schedules = Schedule.objects.filter(name__endswith="Notifications")
    self.assertGreater(schedules.count(), 0)
    for schedule in schedules:
      self.assertTrue(_literal_ok(schedule.args), f"malformed args: {schedule.args!r}")

  def test_existing_malformed_rows_are_repaired(self):
    # rows created before the fix hold bare words; setup must repair them
    Schedule.objects.create(
      name="Test Daily Notifications",
      func="core.tasks.process_batched_notifications",
      args="daily",
      schedule_type=Schedule.DAILY,
      repeats=-1,
    )
    _setup_schedule("daily", "Test Daily Notifications", Schedule.DAILY)
    schedule = Schedule.objects.get(name="Test Daily Notifications")
    self.assertTrue(_literal_ok(schedule.args), f"malformed args: {schedule.args!r}")
