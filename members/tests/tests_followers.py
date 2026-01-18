from django.urls import reverse
from cm_main.utils import get_test_absolute_url
from cm_main.tests.tests_followers import TestFollowersMixin
from cm_main.tests.test_django_q import django_q_sync_class
from .tests_member_base import MemberTestCase


@django_q_sync_class
class TestMemberFollower(TestFollowersMixin, MemberTestCase):
  def do_test_toggle_follow_member(self):
    follower = self.member
    followed = self.create_member(is_active=True)
    # follower follows followed
    url = reverse("members:toggle_follow", args=[followed.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(followed.followers.first(), follower)
    return followed

  def do_test_toggle_unfollow_member(self, followed):
    # test unfollow
    self.client.login(username=self.member.username, password=self.member.password)  # login as follower (ie self.member)
    url = reverse("members:toggle_follow", args=[followed.id])
    response = self.client.post(url, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(followed.followers.count(), 0)

  def test_follow_member(self):
    """Tests that the follow member view works correctly."""
    follower = self.member
    followed = self.do_test_toggle_follow_member()
    followed_url = get_test_absolute_url(reverse("members:detail", args=[followed.id]))
    # now check the email to the owner to inform about the new follower
    self.check_new_follower_email(
      follower=follower,
      owner=followed,
      followed_object=followed,
      followed_url=followed_url,
    )

    # test unfollow
    self.do_test_toggle_unfollow_member(followed)
