from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils.translation import gettext as _

from members.models import Member
from members.tests.tests_member_base import MemberTestCase
from ..forms import ContactForm


class TestContactForm(MemberTestCase):
  def test_contact_form(self):
    """test the contact form"""
    response = self.client.get(reverse("cm_main:contact"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "cm_main/contact/contact-form.html")

    # test the form with invalid data
    form = ContactForm({
      "name": "John Doe",
      "email": "john.doe@example.com",
    })
    self.assertFormError(form, "message", _("This field is required."))

    # test the form with valid data, message only
    test_msg = "This is a test message."
    response = self.client.post(reverse("cm_main:contact"), {"message": test_msg}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, _("Your message has been sent"))
    # check email
    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].subject, _("Contact form"))
    self.assertEqual(Member.objects.filter(is_superuser=True).first(), self.superuser)
    self.assertSequenceEqual(mail.outbox[0].to, [self.superuser.email])
    for content, type in mail.outbox[0].alternatives:
      if type == "text/html":
        break
    # print(content)
    subject = _("You have a new message from %(name)s (%(email)s). ") % {
      "name": self.member.full_name,
      "email": self.member.email,
    }
    self.assertInHTML(settings.SITE_NAME + " - " + subject, content)
    msg = _("%(sender_name)s sent you the following message from %(site_name)s:") % {
      "sender_name": self.member.full_name,
      "site_name": settings.SITE_NAME,
    }
    test_msg = test_msg.replace("\n", "<br>")
    html_message = f"""<p class="mt-2">
  <strong>{msg}</strong>
  <br>
  <i>{test_msg}</i>
  </p>"""
    self.assertInHTML(html_message, content)
    # reset mailbox
    mail.outbox = []
