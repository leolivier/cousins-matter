import logging
from urllib.parse import unquote

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from core.followers import check_followers
from core.utils import PageOutOfBounds, Paginator

from ..models import ChatRoom, PrivateChatRoom
from ..services import (
  build_room_context,
  do_create_chat_room,
  get_chat_rooms_queryset,
  get_room_messages,
  resolve_first_message_authors,
)

logger = logging.getLogger(__name__)


def list_chat_rooms(request, page_num=1, private=False):
  """
  Renders a page displaying a list of chat rooms (public or private and only the ones the user is
  a member of if private), along with information about the author of the first message in each
  room. This view is accessible only to authenticated users.
  """
  try:
    page = Paginator.get_page(
      request,
      get_chat_rooms_queryset(request.user, private),
      page_num,
      reverse_link="chat:private_chat_page" if private else "chat:chat_page",
      default_page_size=settings.DEFAULT_CHATROOMS_PER_PAGE,
    )
    resolve_first_message_authors(page.object_list)
    return render(request, "chat/chat_rooms.html", {"page": page, "private": private})
  except PageOutOfBounds as exc:
    return redirect(exc.redirect_to)


def create_chat_room(request, private=False):
  """
  Creates a new public or private chat room and redirects to it. On a name collision, displays the
  error message(s) returned by the service and redirects back to the chat rooms list. When a public
  room is newly created, the creator's followers are notified.
  """
  room_name = unquote(request.POST["name"])
  new_room, created, errors = do_create_chat_room(request.user, room_name, private)
  for error in errors:
    messages.error(request, error)
  if new_room is None:
    return redirect(reverse("chat:private_chat_rooms") if private else reverse("chat:chat_rooms"))
  room_url = reverse("chat:private_room" if private else "chat:room", args=[new_room.slug])
  if created and not private:
    logger.debug("public room created, checking followers")
    check_followers(
      request,
      followed_object=new_room,
      followed_object_owner=request.user,
      followed_object_url=room_url,
    )
  return redirect(room_url)


def display_chat_room(request, room_slug, private=False, page_num=None):
  """
  Displays a chat room (private when ``private`` is True). The user must be authenticated; for a
  private room they must be a member, otherwise an error is shown and they are redirected to the
  private chat rooms page.
  """
  room = get_object_or_404(ChatRoom if not private else PrivateChatRoom, slug=room_slug)
  if private and not room.followers.filter(pk=request.user.pk).exists():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  try:
    page = Paginator.get_page(
      request,
      get_room_messages(room),
      page_num,
      reverse_link="chat:room_page",
      compute_link=lambda page_num: reverse("chat:room_page", args=[room_slug, page_num]),
      default_page_size=settings.DEFAULT_CHATMESSAGES_PER_PAGE,
    )
    return render(request, "chat/room_detail.html", build_room_context(room, page, private))
  except PageOutOfBounds as exc:
    return redirect(exc.redirect_to)
