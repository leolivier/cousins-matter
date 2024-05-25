from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib import messages
from urllib.parse import unquote

from cousinsmatter.utils import redirect_to_referer
from .models import ChatMessage, ChatRoom


@login_required
def chat(request):
  chat_rooms = ChatRoom.objects.all()
  return render(request, 'chat/chat.html', {'rooms': chat_rooms})


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
          messages.error(request, f'{error[0]}: {' '.join(error[1])}')
    return redirect_to_referer(request)


@login_required
def chat_room(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  messages = ChatMessage.objects.filter(room=room.id)[0:25]  # TODO: paginate
  return render(request, 'chat/room.html', {'room': room, 'chat_messages': messages})
