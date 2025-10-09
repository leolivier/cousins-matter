import datetime
import logging
import os
from PIL import Image, ImageOps

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from cm_main.utils import remove_accents
from .managers import MemberManager

logger = logging.getLogger(__name__)

# lists of fields for use in other modules
ADDRESS_FIELD_NAMES = {
  'number_and_street': pgettext_lazy('CSV Field', 'number_and_street'),
  'complementary_info': pgettext_lazy('CSV Field', 'address_complementary_info'),
  'zip_code': pgettext_lazy('CSV Field', 'zip_code'),
  'city': pgettext_lazy('CSV Field', 'city'),
  'country': pgettext_lazy('CSV Field', 'country')
}

MANDATORY_MEMBER_FIELD_NAMES = {
  'username': pgettext_lazy('CSV Field', 'username'),
  'email': pgettext_lazy('CSV Field', 'email'),
  'first_name': pgettext_lazy('CSV Field', 'first_name'),
  'last_name': pgettext_lazy('CSV Field', 'last_name'),
  'birthdate': pgettext_lazy('CSV Field', 'birthdate'),
  }

MEMBER_FIELD_NAMES = MANDATORY_MEMBER_FIELD_NAMES | {
  'phone': pgettext_lazy('CSV Field', 'phone'),
  'website': pgettext_lazy('CSV Field', 'website'),
  'family': pgettext_lazy('CSV Field', 'family'),
  'avatar': pgettext_lazy('CSV Field', 'avatar'),
  'deathdate': pgettext_lazy('CSV Field', 'deathdate'),
  'managed_by': pgettext_lazy('CSV Field', 'managed_by')
  }


ALL_FIELD_NAMES = MEMBER_FIELD_NAMES | ADDRESS_FIELD_NAMES


class Family(models.Model):
  name = models.CharField(_('Name'), max_length=72)

  parent = models.ForeignKey('self', verbose_name=_('Parent family'), on_delete=models.CASCADE, null=True, blank=True)

  class Meta:
    verbose_name = _('family')
    verbose_name_plural = _('families')
    ordering = ['name']
    indexes = [
            models.Index(fields=["name"]),
    ]

  def __str__(self) -> str:
    return self.name

  def get_absolute_url(self):
    return reverse("members:family_detail", kwargs={"pk": self.pk})


class Address(models.Model):

  number_and_street = models.CharField(_('Number & Street name'), max_length=120)

  complementary_info = models.CharField(_('Complementary info'), max_length=120, default='', blank=True)

  zip_code = models.CharField(_('Zip code'), max_length=12)

  city = models.CharField(_('City'), max_length=120)

  country = models.CharField(_('Country'), max_length=32)

  def __str__(self) -> str:
    return f"""
{self.number_and_street}
{self.complementary_info}
{self.zip_code}, {self.city}
{self.country}
"""

  def get_absolute_url(self):
    return reverse("members:address_detail", kwargs={"pk": self.pk})

  class Meta:
    verbose_name = _('address')
    verbose_name_plural = _('addresses')
    ordering = ['city', 'zip_code', 'number_and_street']
    indexes = [
            models.Index(fields=["city", "zip_code"]),
        ]


class Member(AbstractUser):
    member_manager = models.ForeignKey('self', verbose_name=_('Member manager'), on_delete=models.CASCADE,
                                       related_name='managed_members', null=True, blank=True, default=None)

    avatar = models.ImageField(upload_to=settings.AVATARS_DIR, blank=True, null=True)

    address = models.ForeignKey(Address, verbose_name=_('Address'), null=True, blank=True, on_delete=models.SET_NULL)

    phone = models.CharField(_('Phone'), max_length=32, blank=True)

    birthdate = models.DateField(_('Birthdate'),
                                 help_text=_("Click on the month name or the year to change them quickly"),
                                 null=True, blank=False)
    # issue 135: manage dead members
    is_dead = models.BooleanField(_('Is dead'), default=False, blank=False, null=False)
    deathdate = models.DateField(_('Death date'), null=True, blank=True)

    website = models.URLField(_('Website'), blank=True)

    family = models.ForeignKey(Family, verbose_name=_('Family'), on_delete=models.CASCADE, null=True, blank=True)

    description = models.TextField(_("Who I am"), max_length=2*1024*1024, blank=True, null=True,
                                   help_text=_("Describe yourself, your likes and dislikes..."))
    hobbies = models.CharField(_("My hobbies"), blank=True, null=True, max_length=256,
                               help_text=_("Provide a list of hobbies separated by commas"))

    privacy_consent = models.BooleanField(_("Privacy consent"), default=False, blank=False, null=False)

    followers = models.ManyToManyField('self', verbose_name=_('Followers'), related_name='following',
                                       symmetrical=False, blank=True)
    # issue #149: manage unaccent indexes
    first_name_unaccent = models.CharField(max_length=150, null=True, blank=True)
    last_name_unaccent = models.CharField(max_length=150, null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "birthdate", "email"]

    objects = MemberManager()

    class Meta:
      verbose_name = _('member')
      verbose_name_plural = _('members')
      ordering = ['last_name', 'first_name']
      indexes = [
        models.Index(fields=["birthdate"]),
        models.Index(fields=["first_name_unaccent"]),
        models.Index(fields=["last_name_unaccent"]),
      ]

    def get_absolute_url(self):
      return reverse("members:detail", kwargs={"pk": self.pk})

    @property
    def avatar_url(self):
      return self.avatar.url if self.avatar else settings.DEFAULT_AVATAR_URL

    @property
    def avatar_mini_url(self):
      if self.avatar:
        components = self.avatar.url.split('/')
        components[-1] = 'mini_' + components[-1]
        return '/'.join(components)
      else:
        return settings.DEFAULT_MINI_AVATAR_URL

    @property
    def avatar_mini_path(self):
      base = os.path.basename(self.avatar.path)
      dirname = os.path.dirname(self.avatar.path)
      return os.path.join(dirname, 'mini_'+base)

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
        if today.month > self.birthdate.month or \
           (today.month == self.birthdate.month and today.day > self.birthdate.day):
          year += 1
        return self.birthdate.replace(year=year)
      return datetime.date(2999, 1, 1)

    @property
    def age(self) -> int:
      today = datetime.date.today()
      years = today.year - self.birthdate.year
      return years if (today >= self.next_birthday) else years-1

    def get_manager(self):
      return self.member_manager if self.member_manager else self

    def clean(self):
      if self.deathdate:
        if self.deathdate < self.birthdate:
          dd = self.deathdate
          bd = self.birthdate
          raise ValueError(_("Death date %(dd)s is before birthdate %(bd)s") % {"dd": dd, "bd": bd})
        self.is_dead = True
        self.deathdate = self.deathdate or datetime.date.today()
        self.is_active = False
      else:
        self.is_dead = False
      # If member is active, set member manager to None
      if self.is_active and self.member_manager is not None:
        logger.debug(f"Cleaning member {self.full_name}: removing member manager")
        self.member_manager = None
      elif not self.is_active and self.member_manager is None:
        # If no member manager and member is inactive, use admin member
        logger.debug(f"Cleaning member {self.full_name}: changing member manager to admin")
        self.member_manager = Member.objects.filter(is_superuser=True).first()
      self.first_name_unaccent = remove_accents(self.first_name)
      self.last_name_unaccent = remove_accents(self.last_name)

    def _resize_avatar(self, max_size, save_path):
      try:
        img = Image.open(self.avatar.path)
        if img.height > max_size or img.width > max_size:
          output_size = (max_size, max_size)
          img.thumbnail(output_size)
          img = ImageOps.exif_transpose(img)  # avoid image rotating
          img.save(save_path)
          logger.debug(f"Resized and saved avatar for {self.full_name} in {save_path}, size: {img.size}")
      except FileNotFoundError:
        raise ValueError(f"Avatar file not found: {self.avatar.path}")
      except Exception as e:
        raise e

    def save(self, *args, **kwargs):
      self.clean()  # clean before save
      super().save(*args, **kwargs)
      if self.avatar:
        # resize avatar
        self._resize_avatar(settings.AVATARS_SIZE, self.avatar.path)
        # generate minified for post/ads/chat
        mini_path = self.avatar_mini_path
        if not os.path.isfile(mini_path):
          self._resize_avatar(settings.AVATARS_MINI_SIZE, mini_path)

    def delete(self, *args, **kwargs):
      self.delete_avatar()
      super().delete(*args, **kwargs)

    def delete_avatar(self):
      if self.avatar:
        if os.path.isfile(self.avatar.path):
          os.remove(self.avatar.path)
        mini_path = self.avatar_mini_path
        if os.path.isfile(mini_path):
          os.remove(mini_path)
        self.avatar = None


class LoginTrace(models.Model):
    user = models.ForeignKey(Member, on_delete=models.CASCADE, db_index=True)
    ip = models.GenericIPAddressField(db_index=True)
    ip_info = models.JSONField(default=dict)
    country_code = models.CharField(max_length=2, blank=True)
    user_agent = models.TextField()
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username + " (" + self.ip + ") at " + str(self.login_at)
