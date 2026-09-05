from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, When, Value, BooleanField
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from asgiref.sync import sync_to_async
from enum import Enum

from members.models import Member
from tenants.scoping import TenantManager, TenantModel


class ChatRoomManager(TenantManager):
  def public(self):
    return self.filter(privatechatroom__isnull=True)

  def private(self):
    return self.filter(privatechatroom__isnull=False)

  async def apublic(self):
    return await self.afilter(privatechatroom__isnull=True)

  async def aprivate(self):
    return await self.afilter(privatechatroom__isnull=False)


class ChatRoom(TenantModel):
  # use ChatRoomManager when using ChatRoom.objects
  objects = ChatRoomManager()

  name = models.CharField(max_length=255)
  slug = models.CharField(max_length=255, blank=True)
  date_added = models.DateTimeField(auto_now_add=True)
  followers = models.ManyToManyField(
    Member, related_name="followed_chat_rooms", blank=True, limit_choices_to={"is_active": True}
  )

  class Meta:
    verbose_name = _("chat room")
    verbose_name_plural = _("chat rooms")
    ordering = ("date_added",)
    indexes = [
      models.Index(fields=["tenant", "slug"]),
    ]
    constraints = [
      models.UniqueConstraint(fields=("tenant", "slug"), name="chat room slugs are unique inside a tenant"),
    ]

  def __str__(self):
    return self.name

  def clean(self):
    self.slug = slugify(self.name)
    # slug uniqueness is now per-tenant (constraint instead of unique=True);
    # raise the same coded ValidationError the create flow expects.
    if self.slug and self.__class__.objects.exclude(pk=self.pk).filter(slug=self.slug).exists():
      raise ValidationError(
        {"slug": _("A room with a similar name already exists.")},
        code="slug",
      )

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
    # `is_public` is a @property whose `hasattr(self, "privatechatroom")` resolves
    # the multi-table-inheritance relation with a DB query, so it must run off the
    # event loop. Wrap the attribute access in a lambda: passing `self.is_public`
    # directly to sync_to_async would resolve the @property to a bool before the
    # call and raise "sync_to_async can only be applied to sync functions".
    return await sync_to_async(lambda: self.is_public)()

  @classmethod
  def FlaggedRooms(cls, *filters):
    return cls.objects.annotate(
      is_private=Case(When(privatechatroom__isnull=False, then=Value(True)), default=Value(False), output_field=BooleanField())
    ).filter(filters)


class MessageStatus(Enum):
  UNREAD = "unread"
  PARTIALLY_READ = "partially"
  READ = "read"


class ChatMessage(TenantModel):
  member = models.ForeignKey(Member, on_delete=models.CASCADE)
  room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
  content = models.TextField(_("message"), max_length=2 * 1024 * 1024)
  date_added = models.DateTimeField(auto_now_add=True)
  date_modified = models.DateTimeField(null=True, blank=True)
  # Recipients (private-room members) who have read this message.
  # The sender is NEVER added here. Used to derive the aggregate read status.
  read_by = models.ManyToManyField(Member, related_name="read_chat_messages", blank=True)

  class Meta:
    ordering = ("date_added",)
    indexes = [
      models.Index(fields=["tenant", "room"]),
    ]

  def __str__(self):
    # room = self.room.name if len(self.room.name) < 20 else f'{self.room.name[:20]}...'
    # msg = self.content if len(self.content) < 100 else f'{self.content[:100]}...'
    # return f'{room}:{msg}'
    return f"{self.room}:{self.content}"

  @staticmethod
  def compute_status(is_public, room_members_count, read_count, sender_is_member):
    """Aggregate read status of a message, as seen by its sender.

    Returns a :class:`MessageStatus` value, or ``None`` outside private rooms.
    Recipients = private-room members excluding the sender.

    Pure function (no DB access) shared between sync and async code paths so the
    derivation stays identical whether computed in a view, a consumer or a test.
    """
    if is_public:
      return None
    # denominator = recipients = members minus the sender (if still a member)
    denom = max(room_members_count - 1, 0) if sender_is_member else room_members_count
    if denom <= 0 or read_count <= 0:
      return MessageStatus.UNREAD
    if read_count >= denom:
      return MessageStatus.READ
    return MessageStatus.PARTIALLY_READ

  def read_status(self):
    """Aggregate :class:`MessageStatus` of this message (sender's view).

    Returns ``None`` for public rooms. Queries the DB; when batching a page of
    messages, call :meth:`compute_status` directly with prefetched values to
    avoid N+1 queries (see ``display_chat_room``).
    """
    room = self.room
    if room.is_public:
      return None
    member_ids = set(room.followers.values_list("id", flat=True))
    return ChatMessage.compute_status(
      is_public=False,
      room_members_count=len(member_ids),
      read_count=self.read_by.filter(id__in=member_ids).count(),
      sender_is_member=self.member_id in member_ids,
    )


class PrivateChatRoom(ChatRoom):
  # MTI child: redeclare the scoped manager, else Django falls back to a plain
  # (unscoped) Manager and private-room lookups would cross tenants.
  objects = ChatRoomManager()

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
