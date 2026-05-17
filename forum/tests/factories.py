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

  @factory.post_generation
  def create_thread(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    import random
    from faker import Faker
    fake = Faker()

    # Generate 2 to 8 replies
    from members.tests.factories import MemberFactory
    members = [self.first_message.author]
    while len(members) < 4:
      members.append(MemberFactory())

    for _ in range(random.randint(2, 8)):
      reply = MessageFactory(
        post=self,
        author=random.choice(members),
        content=fake.paragraph()
      )

      # 50% chance of comments
      if random.choice([True, False]):
        for _ in range(random.randint(1, 3)):
          CommentFactory(
            message=reply,
            author=random.choice(members),
            content=fake.sentence()
          )


class CommentFactory(DjangoModelFactory):
  class Meta:
    model = Comment

  author = factory.SubFactory(MemberFactory)
  message = factory.SubFactory(MessageFactory)
  content = factory.Faker("sentence")
