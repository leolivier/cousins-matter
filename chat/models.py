from django.db import models
from django.db.models import Case, When, Value, BooleanField
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from asgiref.sync import sync_to_async
from enum import Enum

from members.models import Member


class ChatRoomManager(models.Manager):
  def public(self):
    return self.filter(privatechatroom__isnull=True)

  def private(self):
    return self.filter(privatechatroom__isnull=False)

  async def apublic(self):
    return await self.afilter(privatechatroom__isnull=True)

  async def aprivate(self):
    return await self.afilter(privatechatroom__isnull=False)


class ChatRoom(models.Model):
  # use ChatRoomManager when using ChatRoom.objects
  objects = ChatRoomManager()

  name = models.CharField(max_length=255)
  slug = models.CharField(max_length=255, blank=True, unique=True)
  date_added = models.DateTimeField(auto_now_add=True)
  followers = models.ManyToManyField(
    Member, related_name="followed_chat_rooms", blank=True, limit_choices_to={"is_active": True}
  )

  class Meta:
    verbose_name = _("chat room")
    verbose_name_plural = _("chat rooms")
    ordering = ("date_added",)
    indexes = [
      models.Index(fields=["slug"]),
    ]

  def __str__(self):
    return self.name

  def clean(self):
    self.slug = slugify(self.name)

  def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)

  @property
  def first_message(self):
    return self.chatmessage_set.first()

  async def afirst_message(self):
    return await sync_to_async(self.first_message)()

  @property
  def owner(self):
    first_message = self.first_message
    return first_message.member if first_message else None

  async def aowner(self):
    first_message = await self.chatmessage_set.afirst()
    return await Member.objects.aget(pk=first_message.member_id) if first_message else None

  @property
  def last_message(self):
    return self.chatmessage_set.last()

  async def alast_message(self):
    return await sync_to_async(self.last_message)()

  @property
  def is_public(self):
    return not hasattr(self, "privatechatroom")

  async def ais_public(self):
    return await sync_to_async(self.is_public)()

  @classmethod
  def FlaggedRooms(cls, *filters):
    return cls.objects.annotate(
      is_private=Case(When(privatechatroom__isnull=False, then=Value(True)), default=Value(False), output_field=BooleanField())
    ).filter(filters)


class MessageStatus(Enum):
  UNREAD = "unread"
  PARTIALLY_READ = "partially"
  READ = "read"


class ChatMessage(models.Model):
  member = models.ForeignKey(Member, on_delete=models.CASCADE)
  room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
  content = models.TextField(_("message"), max_length=2 * 1024 * 1024)
  date_added = models.DateTimeField(auto_now_add=True)
  date_modified = models.DateTimeField(null=True, blank=True)

  class Meta:
    ordering = ("date_added",)
    indexes = [
      models.Index(fields=["room"]),
    ]

  def __str__(self):
    # room = self.room.name if len(self.room.name) < 20 else f'{self.room.name[:20]}...'
    # msg = self.content if len(self.content) < 100 else f'{self.content[:100]}...'
    # return f'{room}:{msg}'
    return f"{self.room}:{self.content}"


class PrivateChatRoom(ChatRoom):
  admins = models.ManyToManyField(Member, related_name="group_chat_rooms_admins", blank=True)

  class Meta:
    verbose_name = _("private chat room")
    verbose_name_plural = _("private chat rooms")

  def members(self):
    return self.followers

  def add_member(self, member):
    self.followers.add(member)

  def remove_member(self, member):
    self.followers.remove(member)
