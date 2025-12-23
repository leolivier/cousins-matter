import logging
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from members.models import Member
from ..models import ChatMessage, ChatRoom

logger = logging.getLogger(__name__)


@login_required
def create_test_rooms(request, num_rooms):
  for i in range(num_rooms):
    ChatRoom(name=f"a chat room #{i}").save()
  return redirect("chat:chat_rooms")


@login_required
def create_test_messages(request, num_messages):
  room = ChatRoom.objects.create(name="A chat room for testing a lot of messages")
  connected_member = Member.objects.get(id=request.user.id)
  for i in range(num_messages):
    ChatMessage(room=room, member=connected_member, content=f"a chat message #{i}").save()
  return redirect("chat:room", args=[room.slug])
