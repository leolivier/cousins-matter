from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils.translation import gettext as _

from members.models import Member
from members.tests.tests_member_base import MemberTestCase
from .forms import ContactForm


def get_absolute_url(url):
  return 'http://testserver%s' % (url)


class TestFollowersMixin():
  def check_followers_emails(self, follower, sender, owner, url, followed_object, created_object, created_content):
    """function to test the followers emails
    - owner should have received an email to say he has a new folllower
    - follower should have received an email because he is following the
      object for which something new has been created by sender
    """
    self.assertEqual(len(mail.outbox), 2)
    # first email is for the owner
    owner_message = mail.outbox[0]
    # second email is for the followers
    follower_message = mail.outbox[1]

    followed_url = get_absolute_url(url)
    followed_type = followed_object._meta.verbose_name
    followed_object_name = str(followed_object)
    obj_type = created_object._meta.verbose_name

    # first email is for the author
    self.assertEqual(owner_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(owner_message.recipients(), [owner.email])
    self.assertSequenceEqual(owner_message.bcc, [])
    subject = _('New follower to your %(followed_type)s \"%(followed_object_name)s\"') % {
        'followed_type': followed_type,
        'followed_object_name': followed_object_name}
    # print("subject", subject)
    self.assertEqual(owner_message.subject, subject)
    for content, type in owner_message.alternatives:
      if type == 'text/html':
        break
    message = _("%(follower_name)s is now following your %(followed_type)s "
                "<a href=\"%(followed_url)s\">\"%(followed_object_name)s\"</a> on %(site_name)s") % {
        'follower_name': follower.get_full_name(),
        'followed_type': followed_type,
        'followed_url': followed_url,
        'followed_object_name': followed_object_name,
        'site_name': settings.SITE_NAME
        }
    html = f'<div class="center"><p class="mt-2">{message}</p></div>'.replace('&quot;', '"')

    # print(content)
    self.assertInHTML(html, content)

    # second email is for the followers, no recipients, only bcc. The owner is considered as implicit follower
    self.assertEqual(follower_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(follower_message.to, [])
    self.assertEqual(len(follower_message.bcc), 2)
    self.assertIn(follower.email, follower_message.bcc)
    self.assertIn(owner.email, follower_message.bcc)
    subject = _('New %(obj_type)s added to %(followed_type)s "%(followed_object_name)s"') % {
                'obj_type': obj_type,
                'followed_object_name': followed_object_name,
                'followed_type': followed_type
              }
    # print("subject", subject)
    self.assertEqual(follower_message.subject, subject)
    for content, type in follower_message.alternatives:
      if type == 'text/html':
        break
    # print("content=", content)
    message = _("%(author_name)s added the following %(obj_type)s on %(followed_type)s "
                "<a href=\"%(followed_object_url)s\">'%(followed_object_name)s'</a>:") % {
      'author_name': sender.get_full_name(),
      'obj_type': obj_type,
      'followed_type': followed_type,
      'followed_object_url': followed_url,
      'followed_object_name': followed_object_name}
    created_content = created_content.replace('\n', '<br>')
    html = f'''<p class="mt-2">
  <strong>{message}</strong>
  <br>
  <i>{created_content}</i>
</p>'''
    self.assertInHTML(html, content)
    # reset mailbox
    mail.outbox = []


class TestContactForm(MemberTestCase):
  def test_contact_form(self):
    """test the contact form"""
    response = self.client.get(reverse('cm_main:contact'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'cm_main/contact-form.html')

    # test the form with invalid data
    form = ContactForm({
      'name': 'John Doe',
      'email': 'john.doe@example.com',
    })
    self.assertFormError(form, 'message', _('This field is required.'))

    # test the form with valid data, message only
    test_msg = 'This is a test message.'
    response = self.client.post(reverse('cm_main:contact'), {'message': test_msg}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, _('Your message has been sent'))
    # check email
    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].subject, _('Contact form'))
    self.assertEqual(Member.objects.filter(is_superuser=True).first(), self.superuser)
    self.assertSequenceEqual(mail.outbox[0].to, [self.superuser.email])
    for content, type in mail.outbox[0].alternatives:
      if type == 'text/html':
        break
    # print(content)
    subject = _("You have a new message from %(name)s (%(email)s). ") % {
           "name": self.member.get_full_name(), "email": self.member.email}
    self.assertInHTML(settings.SITE_NAME + ' - ' + subject, content)
    msg = _("%(sender_name)s sent you the following message from %(site_name)s:") % {
      'sender_name': self.member.get_full_name(),
      'site_name': settings.SITE_NAME,
    }
    html_message = _('''<p class="mt-2">
  <strong>%(msg)s</strong>
  <br>
  <i>%(message)s</i>
  </p>''') % {
      'msg': msg,
      'message': test_msg.replace('\n', '<br>'),
    }
    self.assertInHTML(html_message, content)
    # reset mailbox
    mail.outbox = []
