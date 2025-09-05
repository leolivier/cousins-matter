from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils.translation import gettext as _
from .utils import get_test_absolute_url


class TestFollowersMixin():
  def check_new_follower_email(self, follower, owner, followed_object, followed_url, expected_emails_count=1):
    """function to test the owner received an email to say he has a new folllower"""

    if len(mail.outbox) != expected_emails_count:
      for m in mail.outbox:
        print(m.subject, 'to', m.to, 'bcc', m.bcc)
    self.assertEqual(len(mail.outbox), expected_emails_count)
    owner_message = mail.outbox[0]

    followed_type = followed_object._meta.verbose_name
    followed_object_name = str(followed_object)

    self.assertEqual(owner_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(owner_message.recipients(), [owner.email])
    self.assertSequenceEqual(owner_message.bcc, [])
    # if followed_object is a member and is the owner,
    # then we are in the case of a new follower for a member
    if followed_object == owner:
      subject = _('You have a new follower!')
    else:
      subject = _('New follower to your %(followed_type)s \"%(followed_object_name)s\"') % {
        'followed_type': followed_type,
        'followed_object_name': followed_object_name}
    # print("subject", subject)
    self.assertEqual(owner_message.subject, subject)
    for content, type in owner_message.alternatives:
      if type == 'text/html':
        break
    if followed_object == owner:
      message = _('Hi %(followed_name)s, <br><a href="%(follower_url)s">%(follower_name)s</a> '
                  'is now following you on %(site_name)s!') % {
                  'followed_name': followed_object.full_name,
                  'follower_url': get_test_absolute_url(reverse('members:detail', args=[follower.pk])),
                  'follower_name': follower.full_name,
                  'site_name': settings.SITE_NAME
                  }
    else:
      message = _("%(follower_name)s is now following your %(followed_type)s "
                  "<a href=\"%(followed_url)s\">\"%(followed_object_name)s\"</a> on %(site_name)s") % {
        'follower_name': follower.full_name,
        'followed_type': followed_type,
        'followed_url': followed_url,
        'followed_object_name': followed_object_name,
        'site_name': settings.SITE_NAME
        }
    html = f'<div class="center"><p class="mt-2">{message}</p></div>'.replace('&quot;', '"')

    # print(content)
    self.assertInHTML(html, content)

    mail.outbox.pop(0)  # remove the message from the outbox

  def check_new_content_email(self, follower, sender, owner, followed_url,
                              followed_object, created_object, created_content, expected_emails_count=1):
    """ check email sent the followers, no recipients, only bcc. The owner is considered as implicit follower"""
    if len(mail.outbox) != expected_emails_count:
      for m in mail.outbox:
        print(m.subject, 'to', m.to, 'bcc', m.bcc)
    self.assertEqual(len(mail.outbox), expected_emails_count)
    follower_message = mail.outbox[0]

    followed_object_name = str(followed_object)
    followed_type = followed_object._meta.verbose_name
    obj_type = created_object._meta.verbose_name

    self.assertEqual(follower_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(follower_message.to, [])
    self.assertIn(follower.email, follower_message.bcc)
    self.assertIn(owner.email, follower_message.bcc)
    self.assertEqual(len(follower_message.bcc), 2 if owner != follower else 1)  # only the follower and the owner
    if followed_object == created_object:  # e.g. when creating a chat room or a post
      subject = _('New %(followed_type)s "%(followed_object_name)s"') % {
        'followed_object_name': followed_object_name,
        'followed_type': followed_type
      }
      message = _("%(author_name)s created the following %(followed_type)s "
                  "<a href=\"%(followed_object_url)s\">'%(followed_object_name)s'</a>:"
                  ) % {
                    'author_name': owner.full_name,
                    'followed_type': followed_type,
                    'followed_object_url': followed_url,
                    'followed_object_name': followed_object_name}
    else:  # e.g. when creating a comment or a message
      subject = _('New %(obj_type)s added to %(followed_type)s "%(followed_object_name)s"') % {
        'obj_type': obj_type,
        'followed_object_name': followed_object_name,
        'followed_type': followed_type
      }
      message = _("%(author_name)s added the following %(obj_type)s on %(followed_type)s "
                  "<a href=\"%(followed_object_url)s\">'%(followed_object_name)s'</a>:") % {
                    'author_name': sender.full_name,
                    'obj_type': obj_type,
                    'followed_type': followed_type,
                    'followed_object_url': followed_url,
                    'followed_object_name': followed_object_name}
    self.assertEqual(follower_message.subject, subject)
    for content, type in follower_message.alternatives:
      if type == 'text/html':
        break
    # print("content=", content)
    created_content = created_content.replace('\n', '<br>')
    html = f'''<p class="mt-2">
  <strong>{message}</strong>
  <br>
  <i>{created_content}</i>
</p>
  '''
    # print(content)
    self.assertInHTML(html, content)

    mail.outbox.pop(0)  # remove the message from the outbox

  def check_followers_emails(self, follower, sender, owner, url, followed_object, created_object, created_content):
    """function to test the followers emails
    - owner should have received an email to say he has a new folllower
    - follower should have received an email because he is following the
      object for which something new has been created by sender
    """

    followed_url = get_test_absolute_url(url)

    # first email is for the author
    self.check_new_follower_email(follower, owner, followed_object, followed_url, expected_emails_count=2)

    # second email is for the followers
    self.check_new_content_email(follower, sender, owner, followed_url,
                                 followed_object, created_object, created_content)
