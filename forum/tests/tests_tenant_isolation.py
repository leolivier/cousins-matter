"""Tenant-isolation tests for the forum (TenantModel).

Proves ``Post``/``Message``/``Comment`` honor the tenant-scoped manager:
queryset isolation, tenant auto-assignment, ``unscoped`` escape hatch,
and the default-tenant fallback when saving outside any tenant context.
"""

from django.test import TestCase

from forum.models import Comment, Message, Post
from forum.tests.factories import CommentFactory, MessageFactory, PostFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context


class ForumTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-forum-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-forum-b")
    # factories pin tenant=default, so pass tenant explicitly on every call
    # (including subfactory-built rows) instead of relying on tenant_context
    cls.message_a = MessageFactory(tenant=cls.tenant_a)
    cls.message_b = MessageFactory(tenant=cls.tenant_b)
    cls.post_a = PostFactory(tenant=cls.tenant_a, title="Same title", first_message=cls.message_a)
    cls.post_b = PostFactory(tenant=cls.tenant_b, title="Same title", first_message=cls.message_b)
    cls.comment_a = CommentFactory(tenant=cls.tenant_a, message=cls.message_a)
    cls.comment_b = CommentFactory(tenant=cls.tenant_b, message=cls.message_b)

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      post_ids = set(Post.objects.values_list("id", flat=True))
      message_ids = set(Message.objects.values_list("id", flat=True))
      comment_ids = set(Comment.objects.values_list("id", flat=True))
    self.assertEqual(post_ids, {self.post_a.id})
    self.assertEqual(message_ids, {self.message_a.id})
    self.assertEqual(comment_ids, {self.comment_a.id})

  def test_tenant_assigned_on_create(self):
    m = MessageFactory(post=self.post_a, author=self.message_a.author, tenant=self.tenant_a)
    self.assertEqual(m.tenant_id, self.tenant_a.id)

  def test_unscoped_sees_all(self):
    self.assertEqual(set(Post.unscoped.values_list("id", flat=True)), {self.post_a.id, self.post_b.id})

  def test_save_without_tenant_falls_back_to_default(self):
    # e.g. a script creating a Post outside any tenant_context: lands on default
    message = MessageFactory()  # saved in the default tenant
    p = PostFactory.build(tenant=None, first_message=message)
    p.save()
    self.assertEqual(p.tenant.slug, "default")
