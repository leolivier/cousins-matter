import factory
from factory.django import DjangoModelFactory
from chat.models import ChatRoom, ChatMessage
from members.tests.factories import MemberFactory


class ChatRoomFactory(DjangoModelFactory):
  class Meta:
    model = ChatRoom

  name = factory.Sequence(lambda n: f"Room {n}")
  # slug is handled in clean/save

  @factory.post_generation
  def create_messages(self, create, extracted, **kwargs):
    if not create or extracted is False:
      return

    import random
    from faker import Faker
    fake = Faker()

    # Generate 5 to 15 messages
    from members.tests.factories import MemberFactory
    members = [MemberFactory() for _ in range(3)]

    for _ in range(random.randint(5, 15)):
      ChatMessageFactory(
        room=self,
        member=random.choice(members),
        content=fake.sentence()
      )


class ChatMessageFactory(DjangoModelFactory):
  class Meta:
    model = ChatMessage

  member = factory.SubFactory(MemberFactory)
  room = factory.SubFactory(ChatRoomFactory)
  content = factory.Faker("text")
