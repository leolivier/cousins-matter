import factory
from factory.django import DjangoModelFactory
from core.models import NotificationEvent
from members.tests.factories import MemberFactory
from chat.tests.factories import ChatRoomFactory


class NotificationEventFactory(DjangoModelFactory):
  class Meta:
    model = NotificationEvent

  member = factory.SubFactory(MemberFactory)
  author = factory.SubFactory(MemberFactory)

  # Generic FK is tricky in factories, I'll simplify for now or use a specific model
  followed_object = factory.SubFactory(ChatRoomFactory)
  followed_object_url = factory.Faker("url")
