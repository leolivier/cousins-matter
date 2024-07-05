import os
from django.db import models
import datetime
from PIL import Image, ImageOps
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from django.contrib.auth.models import AbstractUser
from .managers import MemberManager
from django.urls import reverse
import logging
from django.conf import settings

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
  'avatar': pgettext_lazy('CSV Field', 'avatar')
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
    managing_member = models.ForeignKey('self', verbose_name=_('Managing member'), on_delete=models.CASCADE,
                                        related_name='managed_members', null=True, blank=True, default=None)

    avatar = models.ImageField(upload_to=settings.AVATARS_DIR, blank=True, null=True)

    address = models.ForeignKey(Address, verbose_name=_('Address'), null=True, blank=True, on_delete=models.DO_NOTHING)

    phone = models.CharField(_('Phone'), max_length=32, blank=True)

    birthdate = models.DateField(_('Birthdate'),
                                 help_text=_("Click on the month name or the year to change them quickly"),
                                 null=True, blank=False)

    website = models.URLField(_('Website'), blank=True)

    family = models.ForeignKey(Family, verbose_name=_('Family'), on_delete=models.CASCADE, null=True, blank=True)

    description = models.TextField(_("Who I am"), max_length=2*1024*1024, blank=True, null=True,
                                   help_text=_("Describe yourself, your likes and dislikes..."))
    hobbies = models.CharField(_("My hobbies"), blank=True, null=True, max_length=256,
                               help_text=_("Provide a list of hobbies separated by commas"))

    privacy_consent = models.BooleanField(_("Privacy consent"), default=False, blank=False, null=False)

    followers = models.ManyToManyField('self', verbose_name=_('Followers'), related_name='following',
                                       symmetrical=False, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "last_name", "birthdate", "email"]

    objects = MemberManager()

    class Meta:
      verbose_name = _('member')
      verbose_name_plural = _('members')
      ordering = ['last_name', 'first_name']
      indexes = [
        models.Index(fields=["birthdate"]),
      ]

    def get_absolute_url(self):
      return reverse("members:detail", kwargs={"pk": self.pk})

    def avatar_url(self):
      return self.avatar.url if self.avatar else settings.DEFAULT_AVATAR_URL

    def avatar_mini_url(self):
      if self.avatar:
        components = self.avatar.url.split('/')
        components[-1] = 'mini_' + components[-1]
        return '/'.join(components)
      else:
        return settings.DEFAULT_MINI_AVATAR_URL

    def avatar_mini_path(self):
      base = os.path.basename(self.avatar.path)
      dirname = os.path.dirname(self.avatar.path)
      return os.path.join(dirname, 'mini_'+base)

    def __str__(self) -> str:
      return self.get_full_name()

    def next_birthday(self) -> datetime.date:
      today = datetime.date.today()
      year = today.year
      if self.birthdate:
        if today.month > self.birthdate.month or \
           (today.month == self.birthdate.month and today.day > self.birthdate.day):
          year += 1
        return self.birthdate.replace(year=year)
      return datetime.date(2999, 1, 1)

    def age(self) -> int:
      today = datetime.date.today()
      years = today.year - self.birthdate.year
      return years if (today >= self.next_birthday()) else years-1

    def get_manager(self):
      return self.managing_member if self.managing_member else self

    def clean(self):
      # If member is active, set managing member to None
      if self.is_active and self.managing_member is not None:
        logger.debug(f"Cleaning member {self.get_full_name()}: changing managing member to himself")
        self.managing_member = None
      elif not self.is_active and self.managing_member is None:
        # If no managing member and member is inactive, use admin member
        logger.debug(f"Cleaning member {self.get_full_name()}: changing managing member to admin")
        self.managing_member = Member.objects.filter(is_superuser=True).first()

    def _resize_avatar(self, max_size, save_path):
      img = Image.open(self.avatar.path)
      if img.height > max_size or img.width > max_size:
        output_size = (max_size, max_size)
        img.thumbnail(output_size)
        img = ImageOps.exif_transpose(img)  # avoid image rotating
        img.save(save_path)
        logger.debug(f"Resized and saved avatar for {self.get_full_name()} in {save_path}, size: {img.size}")

    def save(self, *args, **kwargs):
      super().save(*args, **kwargs)
      if self.avatar:
        # resize avatar
        self._resize_avatar(settings.AVATARS_SIZE, self.avatar.path)
        # generate minified for post/ads/chat
        mini_path = self.avatar_mini_path()
        if not os.path.isfile(mini_path):
          self._resize_avatar(settings.AVATARS_MINI_SIZE, mini_path)

    def delete(self, *args, **kwargs):
      super().delete(*args, **kwargs)
      if self.avatar:
        if os.path.isfile(self.avatar.path):
          os.remove(self.avatar.path)
        mini_path = self.avatar_mini_path()
        if os.path.isfile(mini_path):
          os.remove(mini_path)
