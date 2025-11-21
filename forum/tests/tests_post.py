from django.urls import reverse
from django.db import transaction
from members.tests.tests_member_base import MemberTestCase
from ..views.views_post import PostCreateView, PostEditView
from ..models import Post, Message, Comment


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
        """Tests creating a new forum post."""
        self.post.refresh_from_db()
        self.message.refresh_from_db()
        self.assertEqual(self.message.post, self.post)
        self.assertEqual(self.post.first_message, self.message)
        self.assertEqual(self.post.title, "a title")
        self.assertEqual(self.message.content, "test message")

    def test_create_post_get_view(self):
        """Tests the get view for creating a new forum post."""
        url = reverse("forum:create")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "forum/post_form.html")
        self.assertIs(response.resolver_match.func.view_class, PostCreateView)

    def test_create_post_view_post(self):
        """Tests the post view for creating a new forum post."""
        url = reverse("forum:create")
        title = "another title"
        content = "another test message"
        response = self.client.post(
            url, {"title": title, "content": content}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        # pprint(vars(response))
        post = Post.objects.filter(title=title)
        self.assertEqual(post.count(), 1)
        post = post.first()
        self.assertEqual(post.first_message.content, content)
        self.assertRedirects(response, reverse("forum:display", args=[post.id]))


class PostEditTestCase(ForumTestCase):
    def test_edit_post_view_get(self):
        """Tests the get view for editing a forum post."""
        url = reverse("forum:edit", args=[self.post.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "forum/post_form.html")
        self.assertIs(response.resolver_match.func.view_class, PostEditView)

    def test_edit_post_view_post(self):
        """Tests the post view for editing a forum post."""
        url = reverse("forum:edit", args=[self.post.id])
        title = "modified title"
        content = "modified test message"
        response = self.client.post(
            url, {"title": title, "content": content}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        # pprint(vars(response))
        post = Post.objects.filter(title=title)
        self.assertEqual(post.count(), 1)
        post = post.first()
        self.assertEqual(post.first_message.content, content)
        self.assertRedirects(response, reverse("forum:display", args=[post.id]))


class PostDeleteTestCase(ForumTestCase):
    def test_delete_post_view(self):
        """Tests the post view for deleting a forum post."""
        url = reverse("forum:delete", args=[self.post.id])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # pprint(vars(response))
        post = Post.objects.filter(id=self.post.id)
        self.assertFalse(post.exists())
        self.assertRedirects(response, reverse("forum:list"))
