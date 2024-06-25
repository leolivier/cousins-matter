from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.core import mail
from django.utils.translation import gettext as _
from forum.tests.tests_post import ForumTestCase
from ..models import Message


def get_absolute_url(url):
  return 'http://testserver%s' % (url)


class PostReplyTestCase(ForumTestCase):
  def test_post_reply(self):
    url = reverse("forum:reply", args=[self.post.id])
    reply_msg_content = 'a reply'
    response = self.client.post(url, {'content': reply_msg_content}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertRedirects(response, reverse('forum:display', args=[self.post.id]))
    msgs = Message.objects.filter(post=self.post)
    self.assertEqual(msgs.count(), 2)
    amsgs = {msg.content for msg in msgs}
    self.assertSetEqual(amsgs, {self.message.content, reply_msg_content},
                        "message contents not equal to what was created")

  def test_edit_reply(self):
    msg = Message(content="a reply to be modified", post=self.post, author=self.member)
    msg.save()
    url = reverse("forum:edit_reply", args=[msg.id])
    reply_msg_content = 'a modified reply'
    with self.assertRaises(ValidationError):
      self.client.post(url, {'content': reply_msg_content})

    response = self.client.post(url, {'content': reply_msg_content}, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
    # pprint(vars(response))
    self.assertEqual(response.status_code, 200)
    self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'reply_id': msg.id, 'reply_str': reply_msg_content}
        )
    msg.refresh_from_db()
    self.assertEqual(msg.content, reply_msg_content)
    # TODO: how to check the edit inside the page which is done in javascript?

  def test_delete_reply(self):
    msg = Message(content="a reply to be deleted", post=self.post, author=self.member)
    msg.save()
    url = reverse("forum:delete_reply", args=[msg.id])
    cnt = Message.objects.filter(post=self.post.id).count()
    with self.assertRaises(ValidationError):
      self.client.post(url)

    response = self.client.post(url, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
    self.assertEqual(response.status_code, 200)
    new_cnt = Message.objects.filter(post=self.post.id).count()
    self.assertEqual(new_cnt, cnt-1)
    self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'reply_id': msg.id}
        )
    # TODO: how to check the removal inside the page which is done in javascript?


class TestFollower(ForumTestCase):

  def test_follow_post(self):
    original_poster = self.member
    self.assertEqual(self.post.first_message.author, original_poster)

    follower = self.create_member_and_login()
    # follower follows the post
    url = reverse("forum:toggle_follow", args=[self.post.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(self.post.followers.filter(username=follower.username).first())
    # self.print_response(response)

    # create yet another member who will post a reply to the post
    new_poster = self.create_member_and_login()
    # poster posts a reply to the post
    url = reverse("forum:reply", args=[self.post.id])
    reply_msg_content = 'a reply'
    response = self.client.post(url, {'content': reply_msg_content}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertRedirects(response, reverse('forum:display', args=[self.post.id]))

    post_title = self.post.title
    message = Message.objects.get(post=self.post, content=reply_msg_content)
    self.assertEqual(message.author, new_poster)
    author = message.author.get_full_name()
    follower_name = follower.get_full_name()
    site_name = settings.SITE_NAME
    post_url = get_absolute_url(reverse('forum:display', args=[self.post.id]))

    # new member 1 should have received an email because he is following the post
    # and original post author should have received an email to say he has a folllower
    self.assertEqual(len(mail.outbox), 2)
    # first email is for the author
    author_message = mail.outbox[0]
    # second email is for the followers
    follower_message = mail.outbox[1]

    # first email is for the author
    self.assertEqual(author_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(author_message.recipients(), [original_poster.email])
    self.assertSequenceEqual(author_message.bcc, [])
    subject = _('New follower to your post "%(post_title)s"') % {'post_title': post_title}
    # print("subject", subject)
    self.assertEqual(author_message.subject, subject)
    for content, type in author_message.alternatives:
      if type == 'text/html':
        break
    html = _('%(follower_name)s is now following your post <a href="%(post_url)s">\"%(post_title)s\"</a> on %(site_name)s') % \
      {'follower_name': follower_name, 'post_title': post_title, 'post_url': post_url, 'site_name': site_name}
    html = f'<div class="center"><p class="mt-2">{html}</p></div>'.replace('&quot;', '"')
    # print(content)
    self.assertInHTML(html, content)

    # second email is for the followers, no recipients, only bcc
    self.assertEqual(follower_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(follower_message.to, [])
    self.assertSequenceEqual(follower_message.bcc, [follower.email])
    subject = _('New reply to post "%(post_title)s"') % {'post_title': post_title}
    # print("subject", subject)
    self.assertEqual(follower_message.subject, subject)
    for content, type in follower_message.alternatives:
      if type == 'text/html':
        break
    # print("content=", content)
    html = _("%(author)s posted the following message on '%(post_title)s':") % {'author': author, 'post_title': post_title}
    reply_msg_content = reply_msg_content.replace('\n', '<br>')
    html = f'''<p class="mt-2">
  <strong>{html}</strong>
  <br>
  <i>{reply_msg_content}</i>
</p>'''
    self.assertInHTML(html, content)

    # login back as self.member
    self.client.logout()
    self.login()
    # reste mailbox
    mail.outbox = []
