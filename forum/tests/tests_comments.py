from django.urls import reverse
from cm_main.tests.tests_followers import TestFollowersMixin
from forum.tests.tests_post import ForumTestCase
from django.core.exceptions import ValidationError
from cm_main.tests.test_django_q import django_q_sync_class

from ..models import Comment


class CommentCreateTestCase(ForumTestCase):
    def tearDown(self):
        Comment.objects.all().delete()
        super().tearDown()

    def test_add_comment_view(self):
        """Tests adding a comment to a forum message."""
        url = reverse("forum:add_comment", args=[self.message.id])
        content = "a wonderful comment"
        response = self.client.post(url, {"content": content}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("forum:display", args=[self.post.id]))
        comment = Comment.objects.filter(message=self.message.id)
        self.assertEqual(comment.count(), 1)
        self.assertEqual(comment.first().content, content)

    def test_edit_comment(self):
        comment = Comment(
            content="a comment to be modified", message=self.message, author=self.member
        )
        comment.save()
        url = reverse("forum:edit_comment", args=[comment.id])
        comment_content = "a modified comment"
        with self.assertRaises(ValidationError):
            self.client.post(url, {"content": comment_content})

        response = self.client.post(
            url,
            {"content": comment_content},
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"},
        )
        # pprint(vars(response))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {"comment_id": comment.id, "comment_str": comment_content},
        )
        comment.refresh_from_db()
        self.assertEqual(comment.content, comment_content)
        # TODO: how to check the edit inside the page which is done in javascript?

    def test_delete_comment(self):
        """Tests deleting a comment from a forum message."""
        comment = Comment(
            content="a comment to be deleted", message=self.message, author=self.member
        )
        comment.save()
        url = reverse("forum:delete_comment", args=[comment.id])
        cnt = Comment.objects.filter(message=self.message.id).count()
        with self.assertRaises(ValidationError):
            self.client.post(url)

        response = self.client.post(url, **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 200)
        new_cnt = Comment.objects.filter(message=self.message.id).count()
        self.assertEqual(new_cnt, cnt - 1)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"), {"comment_id": comment.id}
        )
        # TODO: how to check the removal inside the page which is done in javascript?


@django_q_sync_class
class TestFollower(TestFollowersMixin, ForumTestCase):
    def test_follow_post_on_comment(self):
        """
        Tests that when a follower follows a post and then a member posts a comment on the post,
        the follower receives an email notification.
        """
        original_poster = self.member
        self.assertEqual(self.post.first_message.author, original_poster)

        follower = self.create_member(is_active=True)
        self.client.login(username=follower.username, password=follower.password)
        # follower follows the post
        url = reverse("forum:toggle_follow", args=[self.post.id])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(
            self.post.followers.filter(username=follower.username).first()
        )
        # self.print_response(response)

        # create yet another member who will post a comment to the first message of the post
        member = self.create_member(is_active=True)
        self.client.login(username=member.username, password=member.password)
        # poster posts a comment on the first message to the post
        url = reverse("forum:add_comment", args=[self.post.first_message.id])
        comment_msg_content = "a comment"
        response = self.client.post(url, {"content": comment_msg_content}, follow=True)
        self.assertEqual(response.status_code, 200)

        message = self.post.first_message
        comment = Comment.objects.get(message=message.id, content=comment_msg_content)

        self.check_followers_emails(
            follower=follower,
            sender=comment.author,
            owner=original_poster,
            url=reverse("forum:display", args=[self.post.id]),
            followed_object=self.post,
            created_object=comment,
            created_content=comment_msg_content,
        )
        # login back as self.member
        self.client.login(username=self.member.username, password=self.member.password)
