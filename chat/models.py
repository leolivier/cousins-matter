from django.db import models
from django.db.models import Case, When, Value, BooleanField
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from members.models import Member


class ChatRoomManager(models.Manager):
    def public(self):
        return self.filter(privatechatroom__isnull=True)

    def private(self):
        return self.filter(privatechatroom__isnull=False)

    def apublic(self):
        return self.afilter(privatechatroom__isnull=True)

    def aprivate(self):
        return self.afilter(privatechatroom__isnull=False)


class ChatRoom(models.Model):
  # use ChatRoomManager when using ChatRoom.objects
  objects = ChatRoomManager()

  name = models.CharField(max_length=255)
  slug = models.CharField(max_length=255, blank=True, unique=True)
  date_added = models.DateTimeField(auto_now_add=True)
  followers = models.ManyToManyField(Member, related_name='followed_chat_rooms', blank=True,
                                     limit_choices_to={"is_active": True})

  class Meta:
    verbose_name = _('chat room')
    verbose_name_plural = _('chat rooms')
    ordering = ('date_added',)
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

  def first_message(self):
    return self.chatmessage_set.first()

  def owner(self):
    first_message = self.first_message()
    return first_message.member if first_message else None

  def last_message(self):
    return self.chatmessage_set.last()

  def is_public(self):
    return not self.privatechatroom

  @classmethod
  def FlaggedRooms(cls, *filters):
    return cls.objects.annotate(
      is_private=Case(
        When(privatechatroom__isnull=False, then=Value(True)),
        default=Value(False),
        output_field=BooleanField()
      )).filter(filters)


class ChatMessage(models.Model):
  member = models.ForeignKey(Member, on_delete=models.CASCADE)
  room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
  content = models.TextField(_('message'), max_length=2*1024*1024)
  date_added = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ('date_added',)
    indexes = [
            models.Index(fields=["room"]),
    ]

  def __str__(self):
    # room = self.room.name if len(self.room.name) < 20 else f'{self.room.name[:20]}...'
    # msg = self.content if len(self.content) < 100 else f'{self.content[:100]}...'
    # return f'{room}:{msg}'
    return f'{self.room}:{self.content}'


class PrivateChatRoom(ChatRoom):
  admins = models.ManyToManyField(Member, related_name='group_chat_rooms_admins', blank=True)

  class Meta:
    verbose_name = _('private chat room')
    verbose_name_plural = _('private chat rooms')

  def members(self):
    return self.followers

  def add_member(self, member):
    self.followers.add(member)

  def remove_member(self, member):
    self.followers.remove(member)
