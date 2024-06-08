from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib import messages
from urllib.parse import unquote, urlencode

from cousinsmatter.utils import redirect_to_referer, Paginator
from members.models import Member
from .models import ChatMessage, ChatRoom


@login_required
def chat(request, page_num=1):
  chat_rooms = ChatRoom.objects.all()
  page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_CHATROOMS_PER_PAGE

  ptor = Paginator(chat_rooms, page_size, reverse_link="chat:chat_page")
  if page_num > ptor.num_pages:
      return redirect(reverse('chat:chat_page', args=[ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
  page = ptor.get_page_data(page_num)
  return render(request, 'chat/chat.html', {"page": page})


@login_required
def new_room(request):
  room_name = unquote(request.GET['name'])
  try:
    room = ChatRoom.objects.get_or_create(name=room_name)[0]
    return redirect(reverse('chat:room', args=[room.slug]))
  except ValidationError as ve:
    for error in ve:
      match error[0]:
        case '__all__':
          messages.error(request, ' '.join(error[1]))
        case 'slug':
          print("error on slug:", ' '.join(error[1]))
          pass
        case _:
          messages.error(request, f'{error[0]}: {" ".join(error[1])}')
    return redirect_to_referer(request)


@login_required
def chat_room(request, room_slug, page_num=None):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  messages = ChatMessage.objects.filter(room=room.id)
  page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_CHATMESSAGES_PER_PAGE

  ptor = Paginator(messages, page_size, compute_link=lambda page_num: reverse("chat:room_page", args=[room_slug, page_num]))
  if page_num is None:
    page_num = ptor.num_pages
  elif page_num > ptor.num_pages:
      return redirect(reverse('chat:room_page', args=[room.slug, ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
  page = ptor.get_page_data(page_num)
  return render(request, 'chat/room.html', {'room': room, "page": page})


def test_create_rooms(request, num_rooms):
  for i in range(num_rooms):
    ChatRoom(name=f"a chat room #{i}").save()
  return redirect("chat:chat")


def test_create_messages(request, num_messages):
  room = ChatRoom.objects.create(name="A chat room for testing a lot of messages")
  connected_member = Member.objects.get(id=request.user.id)
  for i in range(num_messages):
    ChatMessage(room=room, member=connected_member,
                content=f"a chat message #{i}").save()
  return redirect("chat:room", args=[room.slug])
