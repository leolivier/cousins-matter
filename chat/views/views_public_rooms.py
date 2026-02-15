import logging
from django.contrib import messages
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django_htmx.http import HttpResponseClientRedirect
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify
from ..models import ChatRoom
from .views_room_common import display_chat_room, list_chat_rooms, create_chat_room
from cm_main import followers
from cm_main.utils import check_edit_permission, confirm_delete_modal

logger = logging.getLogger(__name__)


def chat_rooms(request, page_num=1):
  "See list_chat_rooms in views_room_common"
  return list_chat_rooms(request, page_num=page_num, private=False)


def new_room(request):
  "See create_chat_room in views_room_common"
  return create_chat_room(request, private=False)


def display_public_chat_room(request, room_slug, page_num=None):
  "See display_chat_room in views_room_common"
  return display_chat_room(request, room_slug, private=False, page_num=page_num)


def toggle_follow(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  room_url = reverse("chat:room", args=[room_slug])
  return followers.toggle_follow(request, room, room.owner, room_url)


@require_http_methods(["GET", "PUT"])
def edit_room(request, room_slug):
  assert request.htmx
  room = get_object_or_404(ChatRoom, slug=room_slug)
  if room.owner is not None:  # if the room has no first message, there is no owner
    check_edit_permission(request, room.owner)
  if request.method == "GET":
    return render(request, "chat/room_detail.html#room_edit_form", {"room": room})
  data = QueryDict(request.body)
  # print(data)
  if data.get("trigger", None) == "Escape":  # escape key pressed
    return render(request, "chat/room_detail.html#room_name_display", {"room": room})
  if "room-name" not in data:
    logger.error(f"No room name provided in {request}")
    raise ValidationError("No room name provided")
  room.name = data["room-name"]
  room.slug = slugify(room.name)
  room.save(update_fields=["name", "slug"])
  # return render(request, "chat/room_detail.html#room_name_display", {"room": room})
  # must return a redirect to update the url as the slug has changed
  return HttpResponseClientRedirect(reverse("chat:room", args=[room.slug]))


def delete_room(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  if request.method == "POST":
    if room.owner is not None:  # if the room has no first message, there is no owner
      check_edit_permission(request, room.owner)
    room.delete()
    messages.success(request, f"Chat room {room.name} deleted")
    return HttpResponseClientRedirect(reverse("chat:chat_rooms"))
  else:
    return confirm_delete_modal(
      request,
      _("Room deletion"),
      _('Are you sure you want to delete the room "%(room_name)s" and all its messages?') % {"room_name": room.name},
      room.name,
    )
