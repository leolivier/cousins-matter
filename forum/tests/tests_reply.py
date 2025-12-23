from django.urls import reverse
from django.core.exceptions import ValidationError
from cm_main.tests.tests_followers import TestFollowersMixin
from forum.tests.tests_post import ForumTestCase
from cm_main.tests.test_django_q import django_q_sync_class
from ..models import Message


class PostReplyTestCase(ForumTestCase):
  def test_post_reply(self):
    """Tests replying to a forum post."""
    url = reverse("forum:reply", args=[self.post.id])
    reply_msg_content = "a reply"
    response = self.client.post(url, {"content": reply_msg_content}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertRedirects(response, reverse("forum:display", args=[self.post.id]))
    msgs = Message.objects.filter(post=self.post)
    self.assertEqual(msgs.count(), 2)
    amsgs = {msg.content for msg in msgs}
    self.assertSetEqual(
      amsgs,
      {self.message.content, reply_msg_content},
      "message contents not equal to what was created",
    )

  def test_edit_reply(self):
    """Tests editing a reply to a forum post."""
    msg = Message(content="a reply to be modified", post=self.post, author=self.member)
    msg.save()
    url = reverse("forum:edit_reply", args=[msg.id])
    reply_msg_content = "a modified reply"
    with self.assertRaises(ValidationError):
      self.client.post(url, {"content": reply_msg_content})

    response = self.client.post(
      url,
      {"content": reply_msg_content},
      **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
    )
    # pprint(vars(response))
    self.assertEqual(response.status_code, 200)
    self.assertJSONEqual(
      str(response.content, encoding="utf8"),
      {"reply_id": msg.id, "reply_str": reply_msg_content},
    )
    msg.refresh_from_db()
    self.assertEqual(msg.content, reply_msg_content)
    # TODO: how to check the edit inside the page which is done in javascript?

  def test_delete_reply(self):
    """Tests deleting a reply to a forum post."""
    msg = Message(content="a reply to be deleted", post=self.post, author=self.member)
    msg.save()
    url = reverse("forum:delete_reply", args=[msg.id])
    cnt = Message.objects.filter(post=self.post.id).count()
    with self.assertRaises(ValidationError):
      self.client.post(url)

    response = self.client.post(url, **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"})
    self.assertEqual(response.status_code, 200)
    new_cnt = Message.objects.filter(post=self.post.id).count()
    self.assertEqual(new_cnt, cnt - 1)
    self.assertJSONEqual(str(response.content, encoding="utf8"), {"reply_id": msg.id})
    # TODO: how to check the removal inside the page which is done in javascript?


@django_q_sync_class
class TestFollower(TestFollowersMixin, ForumTestCase):
  def test_follow_post(self):
    """Tests following a forum post."""
    original_poster = self.member
    self.assertEqual(self.post.first_message.author, original_poster)

    follower = self.create_member(is_active=True)
    self.client.login(username=follower.username, password=follower.password)
    # follower follows the post
    url = reverse("forum:toggle_follow", args=[self.post.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(self.post.followers.first(), follower)
    # self.print_response(response)

    # create yet another member who will post a reply to the post
    new_poster = self.create_member(is_active=True)
    self.client.login(username=new_poster.username, password=new_poster.password)
    # poster posts a reply to the post
    url = reverse("forum:reply", args=[self.post.id])
    reply_msg_content = "a reply"
    response = self.client.post(url, {"content": reply_msg_content}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertRedirects(response, reverse("forum:display", args=[self.post.id]))

    message = Message.objects.get(post=self.post, content=reply_msg_content)
    self.assertEqual(message.author, new_poster)

    self.check_followers_emails(
      follower=follower,
      sender=new_poster,
      owner=original_poster,
      url=reverse("forum:display", args=[self.post.id]),
      followed_object=self.post,
      created_object=message,
      created_content=reply_msg_content,
    )

    # login back as self.member
    self.client.login(username=self.member.username, password=self.member.password)
