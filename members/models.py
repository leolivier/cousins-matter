from django.db import models
import datetime
from PIL import Image, ImageOps
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.urls import reverse
import logging
from cousinsmatter import settings

logger = logging.getLogger(__name__)

def get_admin():
   return User.objects.filter(is_superuser=True).first()

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
    return reverse("members:family", kwargs={"pk": self.pk})

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
  class Meta:
    verbose_name = _('address')
    verbose_name_plural = _('addresses')
    ordering = ['city', 'zip_code', 'number_and_street']
    indexes = [
            models.Index(fields=["city", "zip_code"]),
        ]

class Member(models.Model):
    account = models.OneToOneField('auth.User', verbose_name=_('Linked Account'), on_delete=models.CASCADE)

    managing_account = models.ForeignKey('auth.User', verbose_name=_('Managing account'), on_delete=models.CASCADE, 
                                      related_name='managing_account', default=1)
    
    avatar = models.ImageField(default='default.jpg', upload_to=settings.AVATARS_DIR, blank=True)

    address = models.ForeignKey(Address, verbose_name=_('Address'), null=True, blank=True, on_delete=models.DO_NOTHING)

    phone = models.CharField(_('Phone'), max_length=32, blank=True)

    birthdate = models.DateField(_('Birthdate'), null=True, blank=False)
    
    website = models.URLField(_('Website'), blank=True)

    family = models.ForeignKey(Family, verbose_name=_('Family'), on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
      verbose_name = _('member')
      verbose_name_plural = _('members')
      ordering = ['account__last_name', 'account__first_name']
      indexes = [
        models.Index(fields=["account", "birthdate"]),
      ]
      
    def get_absolute_url(self):
      return reverse("members:detail", kwargs={"pk": self.pk})
      
    def get_full_name(self):
        uname = self.account.username if self.account_id else self.id
        return f"{self.first_name()} {self.last_name()} {uname}"

    def get_short_name(self):
        return self.account.username if self.account_id else f'member id: {self.id}'
    
    def first_name(self):
      return self.account.first_name if self.account_id else '?'

    def last_name(self):
      return self.account.last_name if self.account_id else '?'

    def email(self):
      return self.account.email if self.account else ''

    def username(self):
      return self.account.username if self.account else ''

    def __str__(self) -> str:
      return self.get_full_name()

    def next_birthday(self) -> datetime.date:
      today = datetime.date.today()
      year = today.year
      if today.month > self.birthdate.month or \
         (today.month == self.birthdate.month and today.day > self.birthdate.day):
            year += 1
      return self.birthdate.replace(year=year)
    
    def age(self) -> int:
      today = datetime.date.today()
      years = today.year - self.birthdate.year
      return years if (today >= self.next_birthday()) else years-1

    def clean(self):
      # If account is active, set managing account to current member account
      if self.account.is_active and self.managing_account != self.account:
        logger.info(f"Cleaning member {self.get_full_name()}: changing managing account to himself")
        self.managing_account = self.account
      elif self.managing_account is None: 
        # If no managing account and account inactive, use admin account
        logger.info(f"Cleaning member {self.get_full_name()}: changing managing account to admin")
        self.managing_account = get_admin()

    def save(self, *args, **kwargs):
      super().save(*args, **kwargs)
      # resize avatar
      img = Image.open(self.avatar.path)
      if img.height > settings.AVATARS_SIZE or img.width > settings.AVATARS_SIZE:
        output_size = (settings.AVATARS_SIZE, settings.AVATARS_SIZE)
        img.thumbnail(output_size)
        img = ImageOps.exif_transpose(img)  # avoid image rotating
        img.save(self.avatar.path)
        logger.info(f"Resized and saved avatar for {self.get_full_name()} in {self.avatar.path}, size: {img.size}")
