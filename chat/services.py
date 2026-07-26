from django.utils.translation import gettext as _
from members.models import Member


def do_remove_member_from_private_room(room, user=None, username=None):
  if user is None and username is None:
    raise ValueError("User or username must be provided.")
  user = user or Member.objects.get(username=username)  # will raise Member.DoesNotExist if not found

  if room.followers.count() == 1:
    return (
      False,
      _("You are the only member in this private room. Please add another one before removing yourself."),
    )
  elif room.admins.filter(pk=user.pk).exists() and room.admins.count() == 1:
    return (
      False,
      _(
        "You are the only admin in this private room. "
        "If you leave the room, no one will be left. "
        "Please add another admin from the members before you remove yourself."
      ),
    )
  else:
    room.followers.remove(user)
    if room.admins.filter(pk=user.pk).exists():
      room.admins.remove(user)
    room.save()
    return (True, _("You have left the room"))


def do_remove_admin_from_private_room(room, user):
  if room.admins.count() < 2:
    return (
      False,
      _("There must be at least one admin in a private room. Please add another one before removing yourself."),
    )
  else:
    room.admins.remove(user)
    room.save()
    return (True, _("You have been removed from the admins of this private room."))


def do_add_member_to_private_room(room, user):
  room.followers.add(user)
  room.save()
  return (True, _("You have been added to the room."))
