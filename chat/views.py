import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Count, OuterRef, Subquery
from urllib.parse import unquote, urlencode

from cousinsmatter.utils import redirect_to_referer, Paginator, is_ajax
from cm_main import followers
from members.models import Member
from .models import ChatMessage, ChatRoom

logger = logging.getLogger(__name__)


@login_required
def chat(request, page_num=1):
  # Subquery to get the author of the first related ChatMessage instance of a room
  first_msg_auth_subquery = ChatMessage.objects.filter(
    room=OuterRef('pk')
  ).order_by(
      'date_added'
  )[:1].select_related(
        'member'
  ).values('member_id')

  # Annotate room instances with the first message and the number of messages in the room
  chat_rooms = ChatRoom.objects.all().annotate(
    num_messages=Count("chatmessage"),
    first_message_author=Subquery(first_msg_auth_subquery)
    ).order_by('date_added')
  page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_CHATROOMS_PER_PAGE

  ptor = Paginator(chat_rooms, page_size, reverse_link="chat:chat_page")
  if page_num > ptor.num_pages:
      return redirect(reverse('chat:chat_page', args=[ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
  page = ptor.get_page_data(page_num)
  author_ids = [room.first_message_author for room in page.object_list if room.first_message_author is not None]
  # print("author ids", author_ids)
  authors = Member.objects.filter(id__in=author_ids)
  for room in page.object_list:
    if room.first_message_author:
      # print("first msg auth=", room.first_message_author)
      for author in authors:
        # print("author name:", author.username)
        if room.first_message_author == author.id:
          room.first_message_author = author
      # print("final author:", room.first_message_author)
  return render(request, 'chat/chat_rooms.html', {"page": page})


@login_required
def new_room(request):
  room_name = unquote(request.GET['name'])
  try:
    room, created = ChatRoom.objects.get_or_create(name=room_name)
    room_url = reverse('chat:room', args=[room.slug])
    # if room was created, check user followers
    if created:
      logger.debug("room created, checking followers")
      followers.check_followers(request, room, request.user, room_url)
    return redirect(room_url)
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
  elif page_num > ptor.num_pages:  # if page_num is out of range, redirect to last page
      return redirect(reverse('chat:room_page', args=[room.slug, ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
  page = ptor.get_page_data(page_num)
  return render(request, 'chat/room_detail.html', {'room': room, "page": page})


@login_required
def toggle_follow(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  room_url = reverse("chat:room", args=[room_slug])
  return followers.toggle_follow(request, room, room.owner(), room_url)


@login_required
def edit_room(request, room_slug):
  if is_ajax(request):
    room = get_object_or_404(ChatRoom, slug=room_slug)
    # print(request.POST)
    if 'room-name' not in request.POST:
      raise ValidationError("No room name provided")
    room.name = request.POST["room-name"]
    room.save(update_fields=["name"])
    return JsonResponse({"room_name": room.name})
  else:
    raise ValidationError("Forbidden non ajax request")


@login_required
def delete_room(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  room.delete()
  messages.success(request, f"Chat room {room.name} deleted")
  return redirect("chat:chat")


@login_required
def test_create_rooms(request, num_rooms):
  for i in range(num_rooms):
    ChatRoom(name=f"a chat room #{i}").save()
  return redirect("chat:chat")


@login_required
def test_create_messages(request, num_messages):
  room = ChatRoom.objects.create(name="A chat room for testing a lot of messages")
  connected_member = Member.objects.get(id=request.user.id)
  for i in range(num_messages):
    ChatMessage(room=room, member=connected_member,
                content=f"a chat message #{i}").save()
  return redirect("chat:room", args=[room.slug])
