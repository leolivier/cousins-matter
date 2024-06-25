from django.conf import settings
from django.urls import reverse
from forum.tests.tests_post import ForumTestCase
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.core import mail

from ..models import Comment


class CommentCreateTestCase(ForumTestCase):

  def tearDown(self):
    Comment.objects.all().delete()
    super().tearDown()

  def test_add_comment_view(self):
    url = reverse("forum:add_comment", args=[self.message.id])
    content = 'a wonderful comment'
    response = self.client.post(url, {'content': content}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertRedirects(response, reverse('forum:display', args=[self.post.id]))
    comment = Comment.objects.filter(message=self.message.id)
    self.assertEqual(comment.count(), 1)
    self.assertEqual(comment.first().content, content)

  def test_edit_comment(self):
    comment = Comment(content="a comment to be modified", message=self.message, author=self.member)
    comment.save()
    url = reverse("forum:edit_comment", args=[comment.id])
    comment_content = 'a modified comment'
    with self.assertRaises(ValidationError):
      self.client.post(url, {'content': comment_content})

    response = self.client.post(url, {'content': comment_content}, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
    # pprint(vars(response))
    self.assertEqual(response.status_code, 200)
    self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'comment_id': comment.id, 'comment_str': comment_content}
        )
    comment.refresh_from_db()
    self.assertEqual(comment.content, comment_content)
    # TODO: how to check the edit inside the page which is done in javascript?

  def test_delete_comment(self):
    comment = Comment(content="a comment to be deleted", message=self.message, author=self.member)
    comment.save()
    url = reverse("forum:delete_comment", args=[comment.id])
    cnt = Comment.objects.filter(message=self.message.id).count()
    with self.assertRaises(ValidationError):
      self.client.post(url)

    response = self.client.post(url, **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
    self.assertEqual(response.status_code, 200)
    new_cnt = Comment.objects.filter(message=self.message.id).count()
    self.assertEqual(new_cnt, cnt-1)
    self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'comment_id': comment.id}
        )
    # TODO: how to check the removal inside the page which is done in javascript?


class TestFollower(ForumTestCase):

  def test_follow_post_on_comment(self):
    original_poster = self.member
    self.assertEqual(self.post.first_message.author, original_poster)

    follower = self.create_member_and_login()
    # follower follows the post
    url = reverse("forum:toggle_follow", args=[self.post.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(self.post.followers.filter(username=follower.username).first())
    # self.print_response(response)

    # create yet another member who will post a comment to the first message of the post
    self.create_member_and_login()
    # poster posts a comment on the first message to the post
    url = reverse("forum:add_comment", args=[self.post.first_message.id])
    comment_msg_content = 'a comment'
    response = self.client.post(url, {'content': comment_msg_content}, follow=True)
    self.assertEqual(response.status_code, 200)

    post_title = self.post.title
    message = self.post.first_message
    comment = Comment.objects.get(message=message.id, content=comment_msg_content)
    author = comment.author.get_full_name()

    # new member 1 should have received an email because he is following the post
    # and original post author should have received an email to say he has a folllower
    self.assertEqual(len(mail.outbox), 2)
    # first email is for the author, tested somewhere else, don't care

    # second email is for the followers, no recipients, only bcc
    follower_message = mail.outbox[1]
    self.assertEqual(follower_message.from_email, settings.DEFAULT_FROM_EMAIL)
    self.assertSequenceEqual(follower_message.to, [])
    self.assertSequenceEqual(follower_message.bcc, [follower.email])
    subject = _('New comment on post "%(post_title)s"') % {'post_title': post_title}
    # print("subject", subject)
    self.assertEqual(follower_message.subject, subject)
    for content, type in follower_message.alternatives:
      if type == 'text/html':
        break
    # print("content=", content)
    html = _("%(author)s posted the following comment on '%(post_title)s':") % \
      {'author': author, 'post_title': post_title}
    comment_msg_content = comment_msg_content.replace('\n', '<br>')
    html = f'''<p class="mt-2">
  <strong>{html}</strong>
  <br>
  <i>{comment_msg_content}</i>
</p>'''
    self.assertInHTML(html, content)

    # login back as self.member
    self.client.logout()
    self.login()
    # reste mailbox
    mail.outbox = []
