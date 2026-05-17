import factory
from factory.django import DjangoModelFactory
from forum.models import Message, Post, Comment
from members.tests.factories import MemberFactory


class MessageFactory(DjangoModelFactory):
  class Meta:
    model = Message

  author = factory.SubFactory(MemberFactory)
  content = factory.Faker("paragraph")
  # post will be handled by PostFactory


class PostFactory(DjangoModelFactory):
  class Meta:
    model = Post

  title = factory.Faker("sentence")
  first_message = factory.SubFactory(MessageFactory, post=None)

  @factory.post_generation
  def set_message_post(self, create, extracted, **kwargs):
    if create:
      self.first_message.post = self
      self.first_message.save()


class CommentFactory(DjangoModelFactory):
  class Meta:
    model = Comment

  author = factory.SubFactory(MemberFactory)
  message = factory.SubFactory(MessageFactory)
  content = factory.Faker("sentence")
