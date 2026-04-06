from django.test import TestCase
from django.core import mail
from members.models import Member
from core.models import NotificationEvent
from core.followers import do_check_followers
from core.tasks import process_batched_notifications


class NotificationBatchesTest(TestCase):
  def setUp(self):
    self.admin = Member.objects.create_superuser(
      username="admin",
      email="admin@test.com",
      password="password",
      birthdate="1980-01-01",
      first_name="Admin",
      last_name="Test",
    )
    self.user_immediate = Member.objects.create_member(
      username="immediate",
      email="immediate@test.com",
      password="password",
      birthdate="1990-01-01",
      email_batch_frequency=Member.FREQUENCY_IMMEDIATE,
      first_name="Immediate",
      last_name="User",
      is_active=True,
    )
    self.user_hourly = Member.objects.create_member(
      username="hourly",
      email="hourly@test.com",
      password="password",
      birthdate="1990-01-01",
      email_batch_frequency="hourly",
      first_name="Hourly",
      last_name="User",
      is_active=True,
    )
    self.user_disabled = Member.objects.create_member(
      username="disabled",
      email="disabled@test.com",
      password="password",
      birthdate="1990-01-01",
      email_batch_frequency=Member.FREQUENCY_NEVER,
      first_name="Disabled",
      last_name="User",
      is_active=True,
    )

    # Create a dummy followed object (using Member as a proxy for any model)
    self.followed_obj = self.admin
    self.followed_obj.followers.add(self.user_immediate, self.user_hourly, self.user_disabled)

  def test_do_check_followers_distribution(self):
    mail.outbox = []
    NotificationEvent.objects.all().delete()

    do_check_followers(
      followed_object=self.followed_obj,
      followed_object_owner=self.admin,
      followed_object_url="/some/url/",
      new_internal_object=None,
      author=self.admin,
    )

    # Immediate user should get an email (in BCC)
    self.assertEqual(len(mail.outbox), 1)
    self.assertIn(self.user_immediate.email, mail.outbox[0].bcc)
    self.assertNotIn(self.user_hourly.email, mail.outbox[0].bcc)
    self.assertNotIn(self.user_disabled.email, mail.outbox[0].bcc)

    # Hourly user should have a NotificationEvent
    self.assertEqual(NotificationEvent.objects.filter(member=self.user_hourly).count(), 1)
    # Disabled user should have nothing
    self.assertEqual(NotificationEvent.objects.filter(member=self.user_disabled).count(), 0)

  def test_process_batched_notifications(self):
    # Create some events
    NotificationEvent.objects.create(
      member=self.user_hourly,
      followed_object=self.followed_obj,
      author=self.admin,
      followed_object_url="/url/1/",
    )
    NotificationEvent.objects.create(
      member=self.user_hourly,
      followed_object=self.followed_obj,
      author=self.admin,
      followed_object_url="/url/2/",
    )

    mail.outbox = []
    process_batched_notifications("hourly")

    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].to, [self.user_hourly.email])

    # Events should be deleted
    self.assertEqual(NotificationEvent.objects.filter(member=self.user_hourly).count(), 0)

  def test_deleted_object_handling(self):
    # Create an event
    ev = NotificationEvent.objects.create(
      member=self.user_hourly,
      followed_object=self.followed_obj,
      author=self.admin,
      followed_object_url="/url/1/",
    )

    # Delete the followed object (proxied by admin here, let's use another member to avoid deleting admin)
    other_member = Member.objects.create_member(
      username="other",
      email="other@test.com",
      password="password",
      birthdate="1990-01-01",
      first_name="Other",
      last_name="User",
      is_active=True,
    )
    ev.followed_object = other_member
    ev.save()

    other_member.delete()

    mail.outbox = []
    process_batched_notifications("hourly")

    # No email should be sent because the object was deleted
    self.assertEqual(len(mail.outbox), 0)
    # Event should still be cleared
    self.assertEqual(NotificationEvent.objects.filter(member=self.user_hourly).count(), 0)
