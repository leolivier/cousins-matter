import logging

from django.core.exceptions import ValidationError
from django.db.models import Count, Exists, OuterRef, Subquery
from django.utils.text import slugify
from django.utils.translation import gettext as _

from members.models import Member

from .models import ChatMessage, ChatRoom, PrivateChatRoom

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------------
# private room member/admin management
# --------------------------------------------------------------------------------------


def do_remove_member_from_private_room(room, requester, member_name=None):
  if member_name:
    member = Member.objects.get(username=member_name)
  else:
    member = requester

  is_admin = (member == requester) or (room.admins.filter(pk=member.pk).exists())

  if not room.followers.filter(pk=member.pk).exists():
    return (
      False,
      _("This user is not a member of this private room"),
    )

  if room.followers.count() == 1:
    if member == requester:
      return (
        False,
        _("You are the only member in this private room. Please add another one before removing yourself."),
      )
    else:
      return (
        False,
        _("This member is the only one in this private room. Please add another one before removing this one."),
      )
  elif is_admin and room.admins.count() == 1:
    # as this code must be reached only by and admin, if the admin is the only one, it must be the requester
    return (
      False,
      _(
        "You are the only admin in this private room. "
        "If you leave the room, no one will be left. "
        "Please add another admin from the members before you remove yourself."
      ),
    )
  else:
    room.followers.remove(member)
    if is_admin:
      room.admins.remove(member)
    room.save()
    return (
      True,
      (_("You have left the room") if member == requester else _("%s has been removed from the room") % member.full_name),
    )


def do_remove_admin_from_private_room(room, requester, username=None):
  if username:
    member = Member.objects.get(username=username)
  else:
    member = requester

  if not room.admins.filter(pk=member.pk).exists():
    if member == requester:
      return (False, _("You are not an admin of this private room"))
    return (False, _("This member is not an admin of this private room"))

  if room.admins.count() < 2:
    if member == requester:
      return (
        False,
        _(
          "You are the only admin in this private room. If you leave the room, no one "
          + "will be left. Please add another admin from the members before you remove yourself."
        ),
      )
    return (
      False,
      _("There must be at least one admin in a private room. Please add another one before removing yourself."),
    )
  else:
    room.admins.remove(member)
    room.save()
    if member == requester:
      return (True, _("You have been removed from the admins of this private room."))
    return (True, _("%s has been removed from the admins of this private room.") % member.full_name)


def do_add_member_to_private_room(room, user_id):

  if not room.followers.filter(pk=user_id).exists():
    member = Member.objects.get(id=user_id)
    room.followers.add(member)
    room.save()
    return (True, _("You have been added to the room."))
  else:
    return (False, _("This user is already a member of this private room"))


def do_add_admin_to_private_room(room, user_id):

  if not room.followers.filter(pk=user_id).exists():
    return (False, _("Only members of this private room can become admins"))

  elif not room.admins.filter(pk=user_id).exists():
    member = Member.objects.get(id=user_id)
    room.admins.add(member)
    room.save()
    return (True, _("%s has been added as an admin of this private room.") % member.full_name)

  else:
    return (False, _("This user is already an admin of this private room"))


# --------------------------------------------------------------------------------------
# chat room listing
# --------------------------------------------------------------------------------------


def get_chat_rooms_queryset(user, private=False):
  """
  Returns the annotated queryset of chat rooms to list: public rooms, or the private rooms the
  given user is a member of. Each room is annotated with its message count, follower count, the
  author id of its first message (``first_message_author``), and whether the user follows it.
  """
  # Subquery to get the author of the first related ChatMessage instance of a room
  first_msg_auth_subquery = (
    ChatMessage.objects.filter(room=OuterRef("pk")).order_by("date_added")[:1].select_related("member").values("member_id")
  )
  chat_rooms = (
    PrivateChatRoom.objects.filter(followers=user).prefetch_related("admins") if private else ChatRoom.objects.public()
  )
  followers_count_subquery = (
    ChatRoom.objects.filter(pk=OuterRef("pk")).values("pk").annotate(count=Count("followers")).values("count")
  )
  return chat_rooms.annotate(
    num_messages=Count("chatmessage", distinct=True),
    num_followers=Subquery(followers_count_subquery),
    first_message_author=Subquery(first_msg_auth_subquery),
    is_following=Exists(Member.objects.filter(id=user.id, followed_chat_rooms=OuterRef("id"))),
  ).order_by("date_added")


def resolve_first_message_authors(rooms):
  """Replaces each room's ``first_message_author`` (an id) with the matching ``Member`` instance."""
  author_ids = [room.first_message_author for room in rooms if room.first_message_author is not None]
  if not author_ids:
    return
  authors = {author.id: author for author in Member.objects.filter(id__in=author_ids)}
  for room in rooms:
    if room.first_message_author:
      room.first_message_author = authors.get(room.first_message_author)


# --------------------------------------------------------------------------------------
# chat room creation
# --------------------------------------------------------------------------------------


def do_create_chat_room(user, room_name, private=False):
  """
  Creates a public or private chat room for ``user``.

  Returns ``(new_room, created, errors)``: on success ``errors`` is empty and ``new_room`` is the
  created (or pre-existing, same-name) room; on a name/slug collision ``new_room`` is ``None`` and
  ``errors`` lists the messages to display.

  Note: notifying the creator's followers for a newly created public room is left to the caller,
  since it needs the HTTP request (to build the absolute URL).
  """
  room_class = PrivateChatRoom if private else ChatRoom
  try:
    new_room, created = room_class.objects.get_or_create(name=room_name)
    if created:
      if private:
        # if room was created, add user who created it as member (ie followers which is reused for that) and admins
        logger.debug("private room created, adding user who created it as member and admin")
        new_room.followers.add(user)
        new_room.admins.add(user)
        new_room.save()
        # even if room was created, we don't check user followers because:
        # IT MIGHT NOT BE ADAPTED; IF SOMEONE CREATES A PRIVATE ROOM AND DOES NOT WANT TO INVITE HIS/HER FOLLOWERS,
        # NO NEED TO TELL THE FOLLOWERS THAT HE/SHE CREATED THE ROOM WHERE THE FOLLOWER WON'T BE ADDED
      # public room: follower notification is wired by the caller (needs the request)
    else:
      if not private and not new_room.is_public:
        raise ValidationError(_("A private room with almost the same name already exists: %s") % new_room.name)
      elif private and new_room.is_public:
        raise ValidationError(_("A public room with almost the same name already exists: %s") % new_room.name)
    return (new_room, created, [])
  except ValidationError as ve:
    errors = []
    for error in ve:
      match error[0]:
        case "__all__":
          errors.append(" ".join(error[1]))
        case "slug":
          similar_room = room_class.objects.get(slug=slugify(room_name))
          errors.append(
            _("Another room with a similar name already exists ('%(similar_room_name)s'). Please choose a different name.")
            % {"similar_room_name": similar_room.name},
          )
        case _:
          errors.append(f"{error[0]}: {' '.join(error[1])}")
    return (None, False, errors)


# --------------------------------------------------------------------------------------
# chat room display
# --------------------------------------------------------------------------------------


def get_room_messages(room):
  """Ordered queryset of a room's messages, with member and read-by prefetched for rendering."""
  return (
    ChatMessage.objects.filter(room=room.id).order_by("date_added", "id").select_related("member").prefetch_related("read_by")
  )


def build_room_context(room, page, private=False):
  """
  Builds the context for the room detail template from a paginated ``page`` of the room's
  messages: the room owner (author of the first message), the last message's date/sender, the
  follower count, and the per-message read status map (private rooms only).
  """
  first_msg = ChatMessage.objects.filter(room=room.id).order_by("date_added", "id").select_related("member").first()
  last_msg = ChatMessage.objects.filter(room=room.id).order_by("-date_added", "-id").select_related("member").first()
  num_followers = room.followers.count()
  # Precompute each displayed message's aggregate read status (private rooms only)
  # so the read receipts render without N+1 queries. ``read_by`` is prefetched on the page's
  # messages, so ``msg.read_by.all()`` below hits the prefetch cache.
  read_status_map = {}
  if private:
    room_member_ids = set(room.followers.values_list("id", flat=True))
    room_members_count = len(room_member_ids)
    for msg in page.object_list:
      read_status_map[msg.id] = ChatMessage.compute_status(
        is_public=False,
        room_members_count=room_members_count,
        read_count=sum(1 for m in msg.read_by.all() if m.id in room_member_ids),
        sender_is_member=msg.member_id in room_member_ids,
      ).value
  return {
    "num_followers": num_followers,
    "room": room,
    "room_owner": first_msg.member if first_msg else None,
    "page": page,
    "private": private,
    "last_date": last_msg.date_added.strftime("%Y-%m-%d") if last_msg else None,
    "last_sender": last_msg.member.username if last_msg else None,
    "read_status_map": read_status_map,
  }
