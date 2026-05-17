import factory
from factory.django import DjangoModelFactory
from chat.models import ChatRoom, ChatMessage
from members.tests.factories import MemberFactory


class ChatRoomFactory(DjangoModelFactory):
  class Meta:
    model = ChatRoom

  name = factory.Sequence(lambda n: f"Room {n}")
  # slug is handled in clean/save


class ChatMessageFactory(DjangoModelFactory):
  class Meta:
    model = ChatMessage

  member = factory.SubFactory(MemberFactory)
  room = factory.SubFactory(ChatRoomFactory)
  content = factory.Faker("text")
