import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Subquery, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from urllib.parse import unquote, urlencode

from members.models import Member
from ..models import ChatMessage, ChatRoom, PrivateChatRoom
from cousinsmatter.utils import Paginator, assert_request_is_ajax


logger = logging.getLogger(__name__)


@login_required
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
    query = request.GET.get('q', '')
    members = Member.objects.filter(
        followed_chat_rooms=room
    ).filter(
        Q(last_name__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query.split()[-1]) |
        Q(first_name__icontains=query.split()[0])
    ).distinct()[:12]  # Limited to 12 results
    data = [{'id': m.id, 'text': m.full_name} for m in members]
    return JsonResponse({'results': data})


@login_required
def private_chat_rooms(request, page_num=1):
  """
  Renders a page displaying a list of private chat rooms that the user is a member of, along with
  information about the author of the first message in each room. This view is accessible only to
  authenticated users.

  Parameters:
    - `request` (HttpRequest): The HTTP request object.
    - `page_num` (int, optional): The page number of the chat rooms to display. Defaults to 1.

  Returns:
    - `HttpResponse`: The HTTP response object containing the rendered template with the private
      chat rooms and their authors.

  Raises:
    - `None`

  """
  # Subquery to get the author of the first related ChatMessage instance of a private room
  first_msg_auth_subquery = ChatMessage.objects.filter(
    room=OuterRef('pk')
  ).order_by(
      'date_added'
  )[:1].select_related(
        'member'
  ).values('member_id')
  # look for private rooms of which the user who sent the request is member
  private_chat_rooms = PrivateChatRoom.objects.filter(followers=request.user)
  # Annotate room instances with the first message and the number of messages in the room
  private_chat_rooms = private_chat_rooms.annotate(
    num_messages=Count("chatmessage"),
    first_message_author=Subquery(first_msg_auth_subquery)
    ).order_by('date_added')
  page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_CHATROOMS_PER_PAGE

  ptor = Paginator(private_chat_rooms, page_size, reverse_link="chat:private_chat_page")
  if page_num > ptor.num_pages:
      return redirect(reverse('chat:private_chat_page', args=[ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
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
  return render(request, 'chat/chat_rooms.html', {"page": page, 'private': True})


@login_required
def new_private_room(request):
  """
  Creates a new private chat room with the given name for the authenticated user.

  Args:
      request (HttpRequest): The HTTP request object containing the 'name' parameter
                             in the GET request.

  Returns:
      HttpResponse: The HTTP response object redirecting to the newly created private
                    chat room.

  Raises:
      ValidationError: If the room name is invalid.

  """
  private_room_name = unquote(request.GET['name'])
  try:
    private_room, created = PrivateChatRoom.objects.get_or_create(name=private_room_name)
    room_url = reverse('chat:private_room', args=[private_room.slug])
    if created:  # if room was created, add user who created it as member (ie followers which is reused for that) and admins
      private_room.followers.add(request.user)
      private_room.admins.add(request.user)
      private_room.save()
      # even if room was created, we don't check user followers because:
      # IT MIGHT NOT BE ADAPTED; IF SOMEONE CREATES A PRIVATE ROOM AND DOES NOT WANT TO INVITE HIS/HER FOLLOWERS,
      # NO NEED TO TELL THE FOLLOWERS THAT HE/SHE CREATED THE ROOM WHERE THE FOLLOWER WON'T BE ADDED
      #   followers.check_followers(request, private_room, request.user, room_url)
    return redirect(room_url)
  except ValidationError as ve:
    for error in ve:
      match error[0]:
        case '__all__':
          messages.error(request, ' '.join(error[1]))
        case 'slug':
          similar_room = ChatRoom.objects.get(slug=slugify(private_room_name))
          messages.error(request,
                         _(f"Another room with a similar name already exists ('{similar_room.name}'). "
                           "Please choose a different name."))
        case _:
          messages.error(request, f'{error[0]}: {" ".join(error[1])}')
    return redirect(reverse('chat:private_chat_rooms'))


@login_required
def private_chat_room(request, room_slug, page_num=None):
  """
  View function for displaying a private chat room.

  The user must be authenticated to access this view.

  Parameters:
      request (HttpRequest): The HTTP request object.
      room_slug (str): The slug of the private chat room.
      page_num (int, optional): The page number of the chat messages to display. Defaults to None.

  Returns:
      HttpResponse: The HTTP response object containing the rendered template for the private chat room.

  Raises:
      Http404: If the private chat room with the given slug does not exist.

  This function retrieves the private chat room with the given slug using `get_object_or_404` from the `PrivateChatRoom` model.
  It checks if the authenticated user is a member of the private chat room by checking if the user is present in the
  `followers` field of the room.
  If the user is not a member, an error message is displayed and the user is redirected to the private chat rooms page.

  The function then retrieves the chat messages for the private chat room and calculates the page size for displaying the
  messages. The page size is either retrieved from the `page_size` parameter in the request GET parameters or from the
  `DEFAULT_CHATMESSAGES_PER_PAGE` setting.

  The function creates a paginator object `ptor` using the `Paginator` class from Django, passing the chat messages and the
  page size as arguments. It also defines a lambda function `compute_link` to generate the link for each page.

  If the `page_num` parameter is not provided, the function sets it to the total number of pages in the paginator.
  If the `page_num` is out of range, the function redirects the user to the last page.

  Finally, the function retrieves the page data for the specified page number using the `get_page_data` method of the
  paginator object and renders the template `chat/room_detail.html` with the room and page data as context.

  Note: The `reverse` function is used to generate URLs for redirecting the user. The `urlencode` function is used to encode
  the query parameters for the URL.
  """
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))
  message_list = ChatMessage.objects.filter(room=room.id)
  page_size = int(request.GET["page_size"]) if "page_size" in request.GET else settings.DEFAULT_CHATMESSAGES_PER_PAGE

  ptor = Paginator(message_list, page_size,
                   compute_link=lambda page_num: reverse("chat:room_page", args=[room_slug, page_num]))
  if page_num is None:
    page_num = ptor.num_pages
  elif page_num > ptor.num_pages:  # if page_num is out of range, redirect to last page
      return redirect(reverse('chat:room_page', args=[room.slug, ptor.num_pages]) + '?' + urlencode({'page_size': page_size}))
  page = ptor.get_page_data(page_num)
  return render(request, 'chat/room_detail.html', {'room': room, "page": page, "private": True})


@login_required
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
    return redirect(reverse('chat:private_chat_rooms'))
  return render(request, 'chat/private/room_members.html', {'room': room})


@login_required
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

  if request.method != 'POST':
    raise ValidationError(_('Method not allowed'))

  room = get_object_or_404(PrivateChatRoom, slug=room_slug)

  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))

  member_id = request.POST.get('member-id')
  member = get_object_or_404(Member, id=member_id)

  if member not in room.followers.all():
    room.followers.add(member)
    room.save()
  else:
    messages.warning(request, _("This user is already a member of this private room"))
  return redirect(reverse('chat:private_room_members', args=[room.slug]))


@login_required
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
    return redirect(reverse('chat:private_chat_rooms'))
  member = get_object_or_404(Member, id=member_id)
  if member in room.followers.all():
    if room.followers.count() < 2:
      messages.error(request, _("This member is the only one in this private room. "
                                "Please add another one before removing this one."))
    else:
      room.followers.remove(member)
      if member in room.admins.all():
        room.admins.remove(member)
      room.save()
      messages.success(request, _("%s has been removed from the room") % member.full_name)
  else:
    messages.warning(request, _("This user is not a member of this private room"))
  return redirect(reverse('chat:private_room_members', args=[room.slug]))


@login_required
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
    return redirect(reverse('chat:private_chat_rooms'))
  else:
    if room.followers.count() == 1:
      messages.error(request, _("You are the only member in this private room. "
                                "Please add another one before removing yourself."))
    elif request.user in room.admins.all() and room.admins.count() == 1:
      messages.error(request, _("You are the only admin in this private room. "
                                "If you leave the room, no one will be left. "
                                "Please add another admin from the members before you remove yourself."))
    else:
      room.followers.remove(request.user)
      if request.user in room.admins.all():
        room.admins.remove(request.user)
      room.save()
      messages.success(request, _("You have left the room"))
  return redirect(reverse('chat:private_chat_rooms'))


@login_required
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
    return redirect(reverse('chat:private_chat_rooms'))
  return render(request, 'chat/private/room_admins.html', {'room': room})


@login_required
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

  if request.method != 'POST':
    raise ValidationError(_('Method not allowed'))

  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))

  member_id = request.POST.get('member-id')
  member = get_object_or_404(Member, id=member_id)

  if member not in room.followers.all():
    messages.error(request, _("Only members of this private room can become admins"))
  elif member not in room.admins.all():
    room.admins.add(member)
    room.save()
  else:
    messages.warning(request, _("This user is already a member of this private room"))

  return redirect(reverse('chat:private_room_admins', args=[room.slug]))


@login_required
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
    return redirect(reverse('chat:private_chat_rooms'))
  member = get_object_or_404(Member, id=member_id)

  if member in room.admins.all():
    if room.admins.count() < 2:
      messages.error(request, _("There must be at least one admin in a private room. "
                                "Please add another one before removing this one."))
    else:
      room.followers.remove(member)
      room.save()
  else:
    messages.warning(request, _("This member is not an admin of this private room"))
  return redirect(reverse('chat:private_room_admins', args=[room.slug]))


@login_required
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
    return redirect(reverse('chat:private_chat_rooms'))
  else:
    if room.admins.count() < 2:
      messages.error(request, _("There must be at least one admin in a private room. "
                                "Please add another one before removing yourself."))
    else:
      room.admins.remove(request.user)
      room.save()
      messages.success(request, _("You have been removed from the admins of this private room."))
  return redirect(reverse('chat:private_chat_rooms'))
