from core.tests.ui import PlaywrightTestCase
from chat.tests.factories import ChatRoomFactory
from chat.models import PrivateChatRoom


class ChatUITestBase(PlaywrightTestCase):
  """Base class for Chat UI tests with pre-created test fixtures."""

  def setUp(self):
    super().setUp()

    # Create a public room with messages
    self.public_room = ChatRoomFactory(name="Public Test Room", create_messages=True)

    # Create a private room
    self.private_room = PrivateChatRoom.objects.create(name="Private Test Room")
    self.private_room.followers.add(self.user)
    self.private_room.admins.add(self.user)

    # Create an empty public room
    self.empty_room = ChatRoomFactory(name="Empty Room", create_messages=False)
