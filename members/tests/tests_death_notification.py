from django.urls import reverse
from django.core import mail
from django.utils.translation import gettext as _
from members.tests.tests_member_base import MemberTestCase


class DeathNotificationTests(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.other_member = self.create_member(is_active=True)
    # self.member is already logged in by MemberTestCase.setUp()

  def test_deathdate_field_not_present_for_user(self):
    # self.member is logged in
    response = self.client.get(reverse("members:profile"))
    self.assertNotContains(response, 'name="deathdate"')
    self.assertNotContains(response, 'name="is_dead"')

  def test_deathdate_field_present_for_admin(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)
    # Admin editing other_member
    response = self.client.get(reverse("members:member_edit", args=[self.other_member.id]), follow=True)
    self.assertContains(response, 'name="deathdate"')

  def test_notify_death_view(self):
    url = reverse("members:notify_death", args=[self.other_member.id])

    # GET request
    response = self.client.get(url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/members/notify_death_form.html")

    # POST request
    response = self.client.post(url, {"deathdate": "2023-01-01", "message": "Passed away peacefully."}, follow=True)

    self.assertRedirects(response, reverse("members:detail", args=[self.other_member.id]))
    self.assertContainsMessage(response, "success", _("The administrator has been notified."))

    # Check email
    self.assertEqual(len(mail.outbox), 1)
    email = mail.outbox[0]
    self.assertIn(self.superuser.email, email.to)
    # Check subject content - verifying both English default and potential translated parts or placeholders
    self.assertIn(_("Death notification for %(member)s") % {"member": self.other_member.full_name}, email.subject)

    self.assertIn("Passed away peacefully", email.body)
    self.assertIn("2023-01-01", email.body)

  def test_notify_death_button_visibility(self):
    # self.member is logged in
    response = self.client.get(reverse("members:detail", args=[self.other_member.id]))
    self.assertContains(response, 'data-action="/members/' + str(self.other_member.id) + '/notify-death"')

    self.client.login(username=self.superuser.username, password=self.superuser.password)
    response = self.client.get(reverse("members:detail", args=[self.other_member.id]))
    self.assertNotContains(response, 'data-action="/members/' + str(self.other_member.id) + '/notify-death"')

  def test_notify_death_button_hidden_if_already_dead(self):
    from datetime import date

    self.other_member.deathdate = date.today()
    self.other_member.save()
    # self.member is logged in
    response = self.client.get(reverse("members:detail", args=[self.other_member.id]))
    self.assertNotContains(response, 'data-action="/members/' + str(self.other_member.id) + '/notify-death"')
