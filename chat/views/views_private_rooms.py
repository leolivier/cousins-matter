import logging
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from members.models import Member
from ..models import PrivateChatRoom
from .views_room_common import display_chat_room, list_chat_rooms, create_chat_room
from cm_main.utils import assert_request_is_ajax


logger = logging.getLogger(__name__)


def private_chat_rooms(request, page_num=1):
  "See list_chat_rooms in views_room_common"
  return list_chat_rooms(request, page_num=page_num, private=True)


def new_private_room(request):
  "See create_chat_room in views_room_common"
  return create_chat_room(request, private=True)


def display_private_chat_room(request, room_slug, page_num=None):
  "See display_chat_room in views_room_common"
  return display_chat_room(request, room_slug, private=True, page_num=page_num)


def search_private_members(request, room_slug):
  """
  Search for private members in a given chat room.

  This view is accessible only to authenticated users. It performs an AJAX search
  for private members in a chat room based on the provided query. The search is
  case-insensitive and matches the query against the `last_name`, `first_name`,
  last name's last word, and first name's first word of the `Member` model.
  The results are limited to the first 12 matching members.

  Parameters:
  - `request` (HttpRequest): The HTTP request object.
  - `room_slug` (str): The slug of the chat room to search in.

  Returns:
  - `JsonResponse`: A JSON response containing the search results. The response
    is a dictionary with a single key `'results'` which contains a list of dictionaries
    representing the matching members. Each dictionary contains the `id` and `text`
    fields of the matching member.

  Raises:
  - `ValidationError`: If the request is not an AJAX request.

  """
  assert_request_is_ajax(request)
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  query = request.GET.get("q", "")
  members = (
    Member.objects.filter(followed_chat_rooms=room)
    .filter(
      Q(last_name__icontains=query)
      | Q(first_name__icontains=query)
      | Q(last_name__icontains=query.split()[-1])
      | Q(first_name__icontains=query.split()[0])
    )
    .distinct()[:12]
  )  # Limited to 12 results
  data = [{"id": m.id, "text": m.full_name} for m in members]
  return JsonResponse({"results": data})


def list_private_room_members(request, room_slug):
  """
  Renders the 'chat/private/room_members.html' template with the list of members of a private chat room.

  Args:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.

  Returns:
      HttpResponse: The rendered template with the list of members of the private chat room.

  Raises:
      Http404: If the private chat room with the given slug does not exist.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not a member of the private chat room, an error message is displayed and the user is
        redirected to the 'chat:private_chat_rooms' view.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  return render(request, "chat/private/room_members.html", {"room": room})


def add_member_to_private_room(request, room_slug):
  """
  Add a member to a private chat room.

  This function is a view that allows an authenticated user to add a member to a private chat room.
  The user must be an admin of the private chat room to perform this action.

  Parameters:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.

  Returns:
      HttpResponse: The response that redirects the user to the private room members page.

  Raises:
      ValidationError: If the request method is not POST.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not an admin of the private chat room, an error message is displayed and the user is
        redirected to the 'chat:private_chat_rooms' view.
      - If the member is already a member of the private chat room, a warning message is displayed.
  """

  if request.method != "POST":
    raise ValidationError(_("Method not allowed"))

  room = get_object_or_404(PrivateChatRoom, slug=room_slug)

  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))

  member_id = request.POST.get("member-id")
  member = get_object_or_404(Member, id=member_id)

  if member not in room.followers.all():
    room.followers.add(member)
    room.save()
  else:
    messages.warning(request, _("This user is already a member of this private room"))
  return redirect(reverse("chat:private_room_members", args=[room.slug]))


def remove_member_from_private_room(request, room_slug, member_id):
  """
  Remove a member from a private chat room.

  This function is a view that allows an authenticated user to remove a member from a private chat room.
  The user must be an admin of the private chat room to perform this action.

  Parameters:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.
      member_id (int): The ID of the member to be removed.

  Returns:
      HttpResponse: The response that redirects the user to the private room members page.

  Raises:
      Http404: If the private chat room or the member is not found.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not an admin of the private chat room, an error message is displayed and the user is
        redirected to the 'chat:private_chat_rooms' view.
      - If the member is the only member in the private chat room, an error message is displayed and the user
        is redirected to the 'chat:private_chat_rooms' view.
      - If the member is not a member of the private chat room, a warning message is displayed.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  member = get_object_or_404(Member, id=member_id)
  if member in room.followers.all():
    if room.followers.count() < 2:
      messages.error(
        request,
        _("This member is the only one in this private room. Please add another one before removing this one."),
      )
    else:
      room.followers.remove(member)
      if member in room.admins.all():
        room.admins.remove(member)
      room.save()
      messages.success(request, _("%s has been removed from the room") % member.full_name)
  else:
    messages.warning(request, _("This user is not a member of this private room"))
  return redirect(reverse("chat:private_room_members", args=[room.slug]))


def leave_private_room(request, room_slug):
  """
  Leave a private chat room.

  This function allows an authenticated user to leave a private chat room. The user must be a member of the
  private chat room to perform this action.

  Parameters:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.

  Returns:
      HttpResponse: The response that redirects the user to the private chat rooms page.

  Raises:
      Http404: If the private chat room is not found.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not a member of the private chat room, an error message is displayed and the user is redirected
        to the 'chat:private_chat_rooms' view.
      - If the user is the only member in the private chat room, an error message is displayed and the user is redirected to
        the 'chat:private_chat_rooms' view.
      - If the user is an admin of the private chat room, they are also removed as an admin.
      - The private chat room is saved after the user is removed.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  else:
    if room.followers.count() == 1:
      messages.error(
        request,
        _("You are the only member in this private room. Please add another one before removing yourself."),
      )
    elif request.user in room.admins.all() and room.admins.count() == 1:
      messages.error(
        request,
        _(
          "You are the only admin in this private room. "
          "If you leave the room, no one will be left. "
          "Please add another admin from the members before you remove yourself."
        ),
      )
    else:
      room.followers.remove(request.user)
      if request.user in room.admins.all():
        room.admins.remove(request.user)
      room.save()
      messages.success(request, _("You have left the room"))
  return redirect(reverse("chat:private_chat_rooms"))


def list_private_room_admins(request, room_slug):
  """
  Renders the 'chat/private/room_admins.html' template with the list of admins of a private chat room.

  Args:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.

  Returns:
      HttpResponse: The rendered template with the list of admins of the private chat room.

  Raises:
      Http404: If the private chat room with the given slug does not exist.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not a member of the private chat room, an error message is displayed and the user is redirected
        to the 'chat:private_chat_rooms' view.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  return render(request, "chat/private/room_admins.html", {"room": room})


def add_admin_to_private_room(request, room_slug):
  """
  Adds a member as an admin to a private chat room.

  Args:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.

  Returns:
      HttpResponse: The response that redirects the user to the private room admins page.

  Raises:
      ValidationError: If the request method is not 'POST'.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not an admin of the private chat room, an error message is displayed and the user is
        redirected to the 'chat:private_chat_rooms' view.
      - If the member is not a member of the private chat room, an error message is displayed.
      - If the member is already an admin of the private chat room, a warning message is displayed.

  """

  if request.method != "POST":
    raise ValidationError(_("Method not allowed"))

  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))

  member_id = request.POST.get("member-id")
  member = get_object_or_404(Member, id=member_id)

  if member not in room.followers.all():
    messages.error(request, _("Only members of this private room can become admins"))
  elif member not in room.admins.all():
    room.admins.add(member)
    room.save()
  else:
    messages.warning(request, _("This user is already a member of this private room"))

  return redirect(reverse("chat:private_room_admins", args=[room.slug]))


def remove_admin_from_private_room(request, room_slug, member_id):
  """
  Removes an admin from a private chat room.

  This function is a view that allows an authenticated user to remove an admin from a private chat room.
  The user must be an admin of the private chat room to perform this action.

  Parameters:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.
      member_id (int): The ID of the member to be removed as an admin.

  Returns:
      HttpResponse: The response that redirects the user to the private room admins page.

  Raises:
      Http404: If the private chat room or the member is not found.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not an admin of the private chat room, an error message is displayed and the user is
        redirected to the 'chat:private_chat_rooms' view.
      - If the member is not an admin of the private chat room, a warning message is displayed.
      - If the member is the only admin in the private chat room, an error message is displayed and the user
        is redirected to the 'chat:private_chat_rooms' view.
      - If the member is successfully removed as an admin, the user is redirected to the private room admins
        page.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  member = get_object_or_404(Member, id=member_id)

  if member in room.admins.all():
    if room.admins.count() < 2:
      messages.error(
        request,
        _("There must be at least one admin in a private room. Please add another one before removing this one."),
      )
    else:
      room.followers.remove(member)
      room.save()
  else:
    messages.warning(request, _("This member is not an admin of this private room"))
  return redirect(reverse("chat:private_room_admins", args=[room.slug]))


def leave_private_room_admins(request, room_slug):
  """
  Removes the authenticated user from the admins of a private chat room.

  Parameters:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.

  Returns:
      HttpResponse: The response that redirects the user to the private chat rooms page.

  Raises:
      Http404: If the private chat room with the given slug does not exist.

  Notes:
      - The user must be authenticated to access this view.
      - If the user is not an admin of the private chat room, an error message is displayed and the user is
        redirected to the 'chat:private_chat_rooms' view.
      - If there are less than two admins in the private chat room, an error message is displayed and the user
        is redirected to the 'chat:private_chat_rooms' view.
      - If the user is successfully removed from the admins, a success message is displayed.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse("chat:private_chat_rooms"))
  else:
    if room.admins.count() < 2:
      messages.error(
        request,
        _("There must be at least one admin in a private room. Please add another one before removing yourself."),
      )
    else:
      room.admins.remove(request.user)
      room.save()
      messages.success(
        request,
        _("You have been removed from the admins of this private room."),
      )
  return redirect(reverse("chat:private_chat_rooms"))
