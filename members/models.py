import datetime
import logging

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.fields import CharField
from django.db.models.fields.related import ForeignKey
from django.db.models.indexes import Index
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from core.utils import create_thumbnail

from tenants.models import Tenant
from tenants.scoping import get_current_tenant

from .managers import MemberManager

logger = logging.getLogger(__name__)

# lists of fields for use in other modules
ADDRESS_FIELD_NAMES = {
  "number_and_street": pgettext_lazy("CSV Field", "number_and_street"),
  "complementary_info": pgettext_lazy("CSV Field", "address_complementary_info"),
  "zip_code": pgettext_lazy("CSV Field", "zip_code"),
  "city": pgettext_lazy("CSV Field", "city"),
  "country": pgettext_lazy("CSV Field", "country"),
}

MANDATORY_MEMBER_FIELD_NAMES = {
  "username": pgettext_lazy("CSV Field", "username"),
  "email": pgettext_lazy("CSV Field", "email"),
  "first_name": pgettext_lazy("CSV Field", "first_name"),
  "last_name": pgettext_lazy("CSV Field", "last_name"),
  "birthdate": pgettext_lazy("CSV Field", "birthdate"),
}

MEMBER_FIELD_NAMES = MANDATORY_MEMBER_FIELD_NAMES | {
  "phone": pgettext_lazy("CSV Field", "phone"),
  "website": pgettext_lazy("CSV Field", "website"),
  "family": pgettext_lazy("CSV Field", "family"),
  "avatar": pgettext_lazy("CSV Field", "avatar"),
  "deathdate": pgettext_lazy("CSV Field", "deathdate"),
  "managed_by": pgettext_lazy("CSV Field", "managed_by"),
}


ALL_FIELD_NAMES = MEMBER_FIELD_NAMES | ADDRESS_FIELD_NAMES


class Family(models.Model):
  name: CharField = models.CharField(_("Name"), max_length=72)

  parent: ForeignKey = models.ForeignKey(
    to="members.Family",
    related_name="self",
    verbose_name=_("Parent family"),
    on_delete=models.DO_NOTHING,
    null=True,
    blank=True,
  )

  class Meta:
    verbose_name = _("family")
    verbose_name_plural = _("families")
    ordering: list[str] = ["name"]
    indexes: list[Index] = [
      models.Index(fields=["name"]),
    ]

  def __str__(self) -> str:
    return self.name

  def get_absolute_url(self):
    return reverse("members:family_detail", kwargs={"pk": self.pk})


class Address(models.Model):
  number_and_street = models.CharField(_("Number & Street name"), max_length=120)

  complementary_info = models.CharField(_("Complementary info"), max_length=120, default="", blank=True)

  zip_code = models.CharField(_("Zip code"), max_length=12)

  city = models.CharField(_("City"), max_length=120)

  state = models.CharField(_("State"), max_length=32, blank=True)

  country = models.CharField(_("Country"), max_length=32)

  def __str__(self) -> str:
    return f"""
{self.number_and_street}
{self.complementary_info}
{self.zip_code}, {self.city}
{self.state}, {self.country}
"""

  def get_absolute_url(self):
    return reverse("members:address_detail", kwargs={"pk": self.pk})

  class Meta:
    verbose_name = _("address")
    verbose_name_plural = _("addresses")
    ordering = ["country", "state", "city", "zip_code", "number_and_street"]
    indexes = [
      models.Index(fields=["city"]),
      models.Index(fields=["zip_code"]),
      models.Index(fields=["country"]),
      models.Index(fields=["state"]),
    ]


class Member(AbstractUser):
  FREQUENCY_NEVER = "never"
  FREQUENCY_IMMEDIATE = "immediate"
  FREQUENCY_HOURLY = "hourly"
  FREQUENCY_DAILY = "daily"
  FREQUENCY_WEEKLY = "weekly"
  FREQUENCY_MONTHLY = "monthly"

  FREQUENCY_CHOICES = [
    (FREQUENCY_NEVER, _("Never")),
    (FREQUENCY_IMMEDIATE, _("Immediately")),
    (FREQUENCY_HOURLY, _("Hourly")),
    (FREQUENCY_DAILY, _("Daily")),
    (FREQUENCY_WEEKLY, _("Weekly")),
    (FREQUENCY_MONTHLY, _("Monthly")),
  ]

  class Role(models.TextChoices):
    MEMBER = "member", _("Member")
    ADMIN = "admin", _("Tenant admin")

  role = models.CharField(_("Role"), max_length=16, choices=Role.choices, default=Role.MEMBER)
  tenant = models.ForeignKey(
    "tenants.Tenant",
    verbose_name=_("Tenant"),
    on_delete=models.PROTECT,
    related_name="members",
    editable=False,
  )

  member_manager = models.ForeignKey(
    "self",
    verbose_name=_("Member manager"),
    on_delete=models.CASCADE,
    related_name="managed_members",
    null=True,
    blank=True,
    default=None,
  )

  avatar = models.ImageField(upload_to=settings.AVATARS_DIR, blank=True, null=True)

  address = models.ForeignKey(Address, verbose_name=_("Address"), null=True, blank=True, on_delete=models.SET_NULL)

  phone = models.CharField(_("Phone"), max_length=32, blank=True)

  birthdate = models.DateField(
    _("Birthdate"), help_text=_("Click on the month name or the year to change them quickly"), null=True, blank=False
  )
  # issue 135: manage dead members
  is_dead = models.BooleanField(_("Is dead"), default=False, blank=False, null=False)
  deathdate = models.DateField(_("Death date"), null=True, blank=True)

  website = models.URLField(_("Website"), blank=True)

  family = models.ForeignKey(Family, verbose_name=_("Family"), on_delete=models.CASCADE, null=True, blank=True)

  description = models.TextField(
    _("Who I am"),
    max_length=2 * 1024 * 1024,
    blank=True,
    null=True,
    help_text=_("Describe yourself, your likes and dislikes..."),
  )
  hobbies = models.CharField(
    _("My hobbies"), blank=True, null=True, max_length=256, help_text=_("Provide a list of hobbies separated by commas")
  )

  privacy_consent = models.BooleanField(_("Privacy consent"), default=False, blank=False, null=False)

  followers = models.ManyToManyField(
    "self", verbose_name=_("Followers"), related_name="following", symmetrical=False, blank=True
  )

  # email preferences
  email_batch_frequency = models.CharField(
    _("Email frequency"),
    max_length=10,
    choices=FREQUENCY_CHOICES,
    default=FREQUENCY_IMMEDIATE,
    help_text=_(
      "How often you want to receive email notifications about the followed elements (members, chat messages, etc.)"
    ),
  )

  # Override AbstractUser.username: uniqueness becomes (tenant, username) so the
  # same username may exist in different tenants. Login is by email, so username
  # is a display-only identifier.
  username = models.CharField(
    _("username"),
    max_length=150,
    unique=False,
    help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
    validators=[UnicodeUsernameValidator()],
    error_messages={"unique": _("A user with that username already exists.")},
  )

  USERNAME_FIELD = "username"
  REQUIRED_FIELDS = ["first_name", "last_name", "birthdate", "email"]

  objects = MemberManager()
  unscoped = models.Manager()

  class Meta:
    verbose_name = _("member")
    verbose_name_plural = _("members")
    ordering = ["last_name", "first_name"]
    indexes = [
      models.Index(fields=["birthdate"]),
      models.Index(fields=["first_name"]),
      models.Index(fields=["last_name"]),
      models.Index(fields=["tenant", "last_name", "first_name"]),
    ]
    constraints = [
      models.UniqueConstraint(fields=["tenant", "username"], name="member_tenant_username_uniq"),
    ]

  def get_absolute_url(self):
    return reverse("members:detail", kwargs={"username": self.username})

  @property
  def avatar_url(self):
    return self.avatar.url if self.avatar else settings.DEFAULT_AVATAR_URL

  @property
  def avatar_mini_url(self):
    if self.avatar:
      components = self.avatar.url.split("/")
      components[-1] = "mini_" + components[-1]
      return "/".join(components)
    else:
      return settings.DEFAULT_MINI_AVATAR_URL

  @property
  def avatar_mini_name(self):
    if self.avatar:
      components = self.avatar.name.split("/")
      components[-1] = "mini_" + components[-1]
      return "/".join(components)
    else:
      return settings.DEFAULT_MINI_AVATAR_URL

  @property
  def full_name(self) -> str:
    return self.get_full_name()

  def __str__(self) -> str:
    return self.get_full_name()

  @property
  def next_birthday(self) -> datetime.date:
    today = datetime.date.today()
    year = today.year
    if self.birthdate:
      if today.month > self.birthdate.month or (today.month == self.birthdate.month and today.day > self.birthdate.day):
        year += 1
      try:
        return self.birthdate.replace(year=year)
      except ValueError:
        # Fallback for Feb 29th in non-leap years
        return self.birthdate.replace(year=year, month=2, day=28)
    return datetime.date(2999, 1, 1)

  @property
  def age(self) -> int:
    today = datetime.date.today()
    years = today.year - self.birthdate.year
    return years if (today >= self.next_birthday) else years - 1

  def get_manager(self):
    return self.member_manager if self.member_manager else self

  @property
  def is_tenant_admin(self) -> bool:
    """A tenant admin (role=admin); platform superusers are is_superuser."""
    return self.role == self.Role.ADMIN

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Track avatar name so save() regenerates thumbnails only when the avatar actually
    # changes, not on every save (e.g. allauth updating last_login on login triggers save()).
    self._original_avatar_name = self.avatar.name if self.avatar else None

  def clean(self):
    if self.deathdate:
      if self.deathdate < self.birthdate:
        raise ValueError(
          _("Death date %(dd)s is before birthdate %(bd)s")
          % {
            "dd": self.deathdate,
            "bd": self.birthdate,
          }
        )
      self.is_dead = True
      self.is_active = False
    else:
      self.is_dead = False
    # If member is active, set member manager to None
    if self.is_active and self.member_manager is not None:
      logger.info(f"Cleaning member {self.full_name}: removing member manager of active member")
      self.member_manager = None
    elif not self.is_active and self.member_manager is None:
      # If no member manager and member is inactive, default to a tenant admin of
      # this member's tenant (fallback to any platform superuser). Use `unscoped`
      # because `objects` is tenant-filtered and would miss admins/superusers that
      # live on another tenant.
      logger.info(f"Cleaning member {self.full_name}: setting member manager to admin for inactive member")
      # Use tenant_id (not the .tenant FK accessor) because clean() can run before
      # save() assigns a tenant (e.g. during form full_clean), when self.tenant
      # would raise RelatedObjectDoesNotExist. Fall back to the current request's
      # tenant, then to any platform superuser.
      tenant_id = self.tenant_id
      if tenant_id is None:
        current = get_current_tenant()
        tenant_id = current.pk if current is not None else None
      admin = (
        Member.unscoped.filter(tenant_id=tenant_id, role=Member.Role.ADMIN, is_active=True).first()
        if tenant_id is not None
        else None
      )
      self.member_manager = admin or Member.unscoped.filter(is_superuser=True, is_active=True).first()

  def save(self, *args, **kwargs):
    # Assign the tenant before clean()/super().save(): a Member always belongs to
    # a tenant. Prefer the current request tenant; fall back to the default tenant
    # (management commands, createsuperuser, allauth signup outside a tenant).
    if self.tenant_id is None:
      self.tenant = get_current_tenant() or Tenant.get_default()
    self.clean()  # clean before save
    # Only regenerate thumbnails when the avatar actually changed, so a plain save
    # (e.g. login updating last_login) doesn't read/rewrite the avatar file.
    original_avatar_name = getattr(self, "_original_avatar_name", None)
    current_avatar_name = self.avatar.name if self.avatar else None
    avatar_changed = current_avatar_name != original_avatar_name

    if avatar_changed and self.avatar:
      # resize avatar itself
      self.avatar = create_thumbnail(self.avatar, settings.AVATARS_SIZE)
    super().save(*args, **kwargs)

    if avatar_changed and self.avatar:
      # generate minified for post/ads/chat
      mini = create_thumbnail(self.avatar, settings.AVATARS_MINI_SIZE)
      mini.seek(0)
      from django.core.files.base import ContentFile

      content_file = ContentFile(mini.read())
      saved_path = default_storage.save(self.avatar_mini_name, content_file)
      if saved_path != self.avatar_mini_name:
        logger.error(f"ERROR: saved_path != self.avatar_mini_name: {saved_path} != {self.avatar_mini_name}")
      logger.debug(f"Resized and saved avatar for {self.full_name} in {saved_path}, size: {settings.AVATARS_MINI_SIZE}")

    # Refresh tracking so a subsequent save without change skips thumbnail regeneration
    self._original_avatar_name = self.avatar.name if self.avatar else None

  def delete(self, *args, **kwargs):
    self.delete_avatar()
    super().delete(*args, **kwargs)

  def delete_avatar(self):
    if self.avatar:
      if self.avatar.storage.exists(self.avatar.name):
        default_storage.delete(self.avatar.name)
      if self.avatar.storage.exists(self.avatar_mini_name):
        default_storage.delete(self.avatar_mini_name)
      self.avatar = None


class LoginTrace(models.Model):
  user = models.ForeignKey(Member, on_delete=models.CASCADE, db_index=True)
  # ip = models.GenericIPAddressField(db_index=True)  issue on postgres which stores 127.0.0.1/32 instead of 127.0.0.1
  ip = models.CharField(max_length=39, unique=False, db_index=True)
  ip_info = models.JSONField(default=dict)
  country_code = models.CharField(max_length=2, blank=True)
  user_agent = models.TextField()
  login_at = models.DateTimeField(auto_now_add=True)
  logout_at = models.DateTimeField(blank=True, null=True)

  def __str__(self):
    return self.user.username + " (" + self.ip + ") at " + str(self.login_at)
