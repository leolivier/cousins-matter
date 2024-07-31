import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from urllib.parse import unquote, urlencode

from members.models import Member
from ..models import ChatMessage, PrivateChatRoom
from cousinsmatter.utils import Paginator


logger = logging.getLogger(__name__)


@login_required
def private_chat_rooms(request, page_num=1):
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
  private_room_name = unquote(request.GET['name'])
  try:
    private_room, created = PrivateChatRoom.objects.get_or_create(name=private_room_name)
    if created:  # if room was created, add user who created it as member (ie followers which is reused for that) and admins
      private_room.followers.add(request.user)
      private_room.admins.add(request.user)
      private_room.save()

    room_url = reverse('chat:private_room', args=[private_room.slug])
    # if room was created, check user followers
    # ### MAYBE NOT ADAPTED; IF SOMEONE CREATES A PRIVATE ROOM AND DOES NOT WANT TO INVITE HIS/HER FOLLOWERS,
    # ### NO NEED TO TELL THE FOLLOWERS THAT HE/SHE CREATED THE ROOM WHERE THE FOLLOWER WON'T BE ADDED
    # if created:
    #   logger.debug("private room created, checking followers")
    #   followers.check_followers(request, private_room, request.user, room_url)
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
    return redirect(reverse('chat:private_chat_rooms'))


@login_required
def private_chat_room(request, room_slug, page_num=None):
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
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))
  return render(request, 'chat/private/room_members.html', {'room': room, 'members': room.followers.all()})


@login_required
def add_member_to_private_room(request, room_slug, member_id):
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))
  member = get_object_or_404(Member, id=member_id)
  if member not in room.followers.all():
    room.followers.add(member)
    room.save()
  else:
    messages.warning(request, _("This user is already a member of this private room"))
  return redirect(reverse('chat:private_room_members', args=[room.slug]))


@login_required
def remove_member_from_private_room(request, room_slug, member_id):
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
  else:
    messages.warning(request, _("This user is not a member of this private room"))
  return redirect(reverse('chat:privat_room_members', args=[room.slug]))


@login_required
def leave_private_room(request, room_slug):
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))
  else:
    if room.followers.count() < 2:
      messages.error(request, _("You are the only member in this private room. "
                                "Please add another one before removing yourself."))
    else:
      room.followers.remove(request.user)
      if request.user in room.admins.all():
        room.admins.remove(request.user)
      room.save()
  return redirect(reverse('chat:private_chat_rooms'))


@login_required
def list_private_room_admins(request, room_slug):
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.followers.all():
    messages.error(request, _("You are not a member of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))
  return render(request, 'chat/private/room_admins.html', {'room': room, 'admins': room.admins.all()})


@login_required
def add_admin_to_private_room(request, room_slug, member_id):
  room = get_object_or_404(PrivateChatRoom, slug=room_slug)
  if request.user not in room.admins.all():
    messages.error(request, _("You are not an admin of this private room"))
    return redirect(reverse('chat:private_chat_rooms'))
  member = get_object_or_404(Member, id=member_id)
  if member not in room.followers.all():
    messages.errors(request, _("Only members of this private room can become admins"))
  if member not in room.admins.all():
    room.admins.add(member)
    room.save()
  else:
    messages.warning(request, _("This user is already a member of this private room"))

  return redirect(reverse('chat:private_room_admins', args=[room.slug]))


@login_required
def remove_admin_from_private_room(request, room_slug, member_id):
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
