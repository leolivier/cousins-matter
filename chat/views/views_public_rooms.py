import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.text import slugify

from members.models import Member
from ..models import ChatMessage, ChatRoom
from cousinsmatter.utils import Paginator, is_ajax
from cm_main import followers

from urllib.parse import unquote, urlencode

logger = logging.getLogger(__name__)


@login_required
def chat_rooms(request, page_num=1):
  # Subquery to get the author of the first related ChatMessage instance of a room
  first_msg_auth_subquery = ChatMessage.objects.filter(
    room=OuterRef('pk')
  ).order_by(
      'date_added'
  )[:1].select_related(
        'member'
  ).values('member_id')

  # Annotate room instances with the first message and the number of messages in the room
  chat_rooms = ChatRoom.objects.public().annotate(
    num_messages=Count("chatmessage"),
    first_message_author=Subquery(first_msg_auth_subquery)
    ).order_by('date_added')

  page = Paginator.get_page(request,
                            object_list=chat_rooms,
                            page_num=page_num,
                            reverse_link="chat:chat_page",
                            default_page_size=settings.DEFAULT_CHATROOMS_PER_PAGE)
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
    if not room.is_public():
      raise ValidationError(_("A private room with almost the same name already exists: %s") % room.name)
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
          similar_room = ChatRoom.objects.get(slug=slugify(room_name))
          messages.error(request,
                         _(f"Another room with a similar name already exists ('{similar_room.name}'). "
                           "Please choose a different name."))
        case _:
          messages.error(request, f'{error[0]}: {" ".join(error[1])}')
    return redirect(reverse('chat:chat_rooms'))


@login_required
def chat_room(request, room_slug, page_num=None):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  messages = ChatMessage.objects.filter(room=room.id)

  page = Paginator.get_page(request,
                            object_list=messages,
                            page_num=page_num,
                            reverse_link="chat:room_page",
                            compute_link=lambda page_num: reverse("chat:room_page", args=[room_slug, page_num]),
                            default_page_size=settings.DEFAULT_CHATMESSAGES_PER_PAGE)
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
    if request.user != room.owner():
      raise ValidationError(_("Only the owner of a room can edit it"))
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
  if request.user != room.owner():
    messages.error(request, _("Only the owner of a room can delete it"))
    return redirect(reverse('chat:chat_rooms'))
  room.delete()
  messages.success(request, f"Chat room {room.name} deleted")
  return redirect('chat:chat_rooms')
