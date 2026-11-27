from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase

from core.mailer import send_mail_async, send_multi_alternatives_async


class SendMailAsyncTests(SimpleTestCase):
  def setUp(self):
    mail.outbox.clear()

  def test_sync_mode_sends_inline(self):
    with self.settings(Q_CLUSTER={"sync": True}):
      sent = send_mail_async("Subject", "Body", recipient_list=["a@example.com"], html_message="<p>Body</p>")
    self.assertEqual(sent, 1)
    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].subject, "Subject")
    self.assertEqual(mail.outbox[0].to, ["a@example.com"])
    self.assertEqual(mail.outbox[0].alternatives[0][0], "<p>Body</p>")

  def test_async_mode_queues_on_qcluster(self):
    with self.settings(Q_CLUSTER={"sync": False}), patch("core.mailer.async_task", return_value="task-1") as queued:
      sent = send_mail_async("Subject", "Body", recipient_list=["a@example.com"], html_message="<p>Body</p>")
    self.assertEqual(sent, "task-1")
    queued.assert_called_once()
    self.assertEqual(queued.call_args.args[0], "django.core.mail.send_mail")
    self.assertEqual(queued.call_args.args[1], "Subject")
    self.assertEqual(queued.call_args.kwargs["html_message"], "<p>Body</p>")
    self.assertEqual(mail.outbox, [])

  def test_queue_failure_falls_back_to_sync_send(self):
    with self.settings(Q_CLUSTER={"sync": False}), patch("core.mailer.async_task", side_effect=RuntimeError("redis down")):
      sent = send_mail_async("Subject", "Body", recipient_list=["a@example.com"])
    self.assertEqual(sent, 1)
    self.assertEqual(len(mail.outbox), 1)

  def test_lazy_translations_are_resolved_before_queueing(self):
    from django.utils.translation import gettext_lazy as _

    with self.settings(Q_CLUSTER={"sync": False}), patch("core.mailer.async_task", return_value="task-1") as queued:
      send_mail_async(_("Subject"), _("Body"), recipient_list=["a@example.com"])
    self.assertIsInstance(queued.call_args.args[1], str)
    self.assertIsInstance(queued.call_args.args[2], str)

  def test_multi_alternatives_uses_bcc(self):
    with self.settings(Q_CLUSTER={"sync": True}):
      sent = send_multi_alternatives_async("Subject", "Body", bcc=["a@example.com", "b@example.com"])
    self.assertEqual(sent, 1)
    self.assertEqual(mail.outbox[0].bcc, ["a@example.com", "b@example.com"])
    self.assertEqual(mail.outbox[0].to, [])
