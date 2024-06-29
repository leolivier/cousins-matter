from django.conf import settings
from django.core import mail
from django.utils.translation import gettext as _


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

    # second email is for the followers, no recipients, only bcc
    self.assertEqual(follower_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(follower_message.to, [])
    self.assertSequenceEqual(follower_message.bcc, [follower.email])
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
