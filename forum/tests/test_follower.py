from django.urls import reverse
from cm_main.tests.tests_followers import TestFollowersMixin
from cm_main.tests.test_django_q import django_q_sync_class
from cm_main.utils import get_test_absolute_url
from forum.models import Message, Post
from members.tests.tests_member_base import MemberTestCase


@django_q_sync_class
class TestMemberFollower(TestFollowersMixin, MemberTestCase):
  def test_follow_member(self):
    """Tests that the follow member view works correctly."""
    # setup follower and followed
    follower = self.member
    followed = self.create_member(is_active=True)
    followed.followers.add(follower)

    # now, followed will create a post
    self.client.login(username=followed.username, password=followed.password)
    url = reverse("forum:create")
    post_title = "a post to be followed"
    post_content = "a content of the new post"
    self.client.post(url, {"title": post_title, "content": post_content}, follow=True)

    # now check the email to the follower to inform about the new post
    post = Post.objects.get(title=post_title)
    post_url = reverse("forum:display", args=[post.id])
    self.check_new_content_email(
      follower=follower,
      sender=None,
      owner=followed,
      followed_url=get_test_absolute_url(post_url),
      followed_object=post,
      created_object=post,
      created_content=post_title,
    )

    # now, followed will reply to his own post
    url = reverse("forum:reply", args=[post.id])
    reply_msg_content = "a reply to be followed"
    self.client.post(url, {"content": reply_msg_content}, follow=True)

    message = Message.objects.get(post=post, content=reply_msg_content)
    self.assertEqual(message.author, followed)
    # now check the email to the follower to inform about the new reply
    self.check_new_content_email(
      follower=follower,
      sender=followed,
      owner=followed,
      followed_url=get_test_absolute_url(post_url),
      followed_object=post,
      created_object=message,
      created_content=reply_msg_content,
    )
