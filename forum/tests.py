from django.urls import reverse
from members.tests.tests_member import MemberTestCase
from django.db import transaction
from django.core.exceptions import ValidationError
from forum.views.views_post import PostCreateView, PostEditView
from .models import Post, Message, Comment


class ForumTestCase(MemberTestCase):

  def setUp(self):
    super().setUp()
    with transaction.atomic():
      self.message = Message(content="test message", author=self.member)
      self.message.save()
      self.post = Post(title="a title", first_message=self.message)
      self.post.save()
      self.message.post = self.post
      self.message.save()

  def tearDown(self):
    Post.objects.all().delete()
    Message.objects.all().delete()
    Comment.objects.all().delete()
    super().tearDown()


class PostCreateTestCase(ForumTestCase):
  def test_create_post(self):
    self.post.refresh_from_db()
    self.message.refresh_from_db()
    self.assertEqual(self.message.post, self.post)
    self.assertEqual(self.post.first_message, self.message)
    self.assertEqual(self.post.title, "a title")
    self.assertEqual(self.message.content, "test message")

  def test_create_post_get_view(self):
    url = reverse("forum:create")
    response = self.client.get(url)
    self.assertTemplateUsed(response, 'forum/post_form.html')
    self.assertIs(response.resolver_match.func.view_class, PostCreateView)

  def test_create_post_view_post(self):
    url = reverse("forum:create")
    title = "another title"
    content = "another test message"
    response = self.client.post(url, {'title': title, 'content': content}, follow=True)
    self.assertEqual(response.status_code, 200)
    # pprint(vars(response))
    post = Post.objects.filter(title=title)
    self.assertEqual(post.count(), 1)
    post = post.first()
    self.assertEqual(post.first_message.content, content)
    self.assertRedirects(response, reverse('forum:display', args=[post.id]))


class PostEditTestCase(ForumTestCase):
  def test_edit_post_view_get(self):
    url = reverse("forum:edit", args=[self.post.id])
    response = self.client.get(url)
    self.assertTemplateUsed(response, 'forum/post_form.html')
    self.assertIs(response.resolver_match.func.view_class, PostEditView)

  def test_create_post_view_post(self):
    url = reverse("forum:edit", args=[self.post.id])
    title = "modified title"
    content = "modified test message"
    response = self.client.post(url, {'title': title, 'content': content}, follow=True)
    self.assertEqual(response.status_code, 200)
    # pprint(vars(response))
    post = Post.objects.filter(title=title)
    self.assertEqual(post.count(), 1)
    post = post.first()
    self.assertEqual(post.first_message.content, content)
    self.assertRedirects(response, reverse('forum:display', args=[post.id]))


class PostDeleteTestCase(ForumTestCase):
  def test_delete_post_view(self):
    url = reverse("forum:delete", args=[self.post.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    # pprint(vars(response))
    post = Post.objects.filter(id=self.post.id)
    self.assertFalse(post.exists())
    self.assertRedirects(response, reverse('forum:list'))


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
