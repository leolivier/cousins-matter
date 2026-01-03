import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django_htmx.http import HttpResponseClientRedirect
from ..models import ChatRoom
from .views_room_common import display_chat_room, list_chat_rooms, create_chat_room
from cm_main import followers
from cm_main.utils import assert_request_is_ajax, check_edit_permission

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


@login_required
def toggle_follow(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  room_url = reverse("chat:room", args=[room_slug])
  return followers.toggle_follow(request, room, room.owner(), room_url)


@login_required
def edit_room(request, room_slug):
  assert_request_is_ajax(request)
  room = get_object_or_404(ChatRoom, slug=room_slug)
  check_edit_permission(request, room.owner())
  # print(request.POST)
  if "room-name" not in request.POST:
    raise ValidationError("No room name provided")
  room.name = request.POST["room-name"]
  room.save(update_fields=["name"])
  return JsonResponse({"room_name": room.name})


@login_required
def delete_room(request, room_slug):
  room = get_object_or_404(ChatRoom, slug=room_slug)
  if request.method == "POST":
    check_edit_permission(request, room.owner())
    room.delete()
    messages.success(request, f"Chat room {room.name} deleted")
    return HttpResponseClientRedirect(reverse("chat:chat_rooms"))
  else:
    return render(
      request,
      "cm_main/common/confirm-delete-modal-htmx.html",
      {
        "ays_title": _("Room deletion"),
        "ays_msg": _('Are you sure you want to delete the room "%(room_name)s" and all its messages?')
        % {"room_name": room.name},
        "delete_url": request.get_full_path(),
        # "expected_value": room.name,
      },
    )
