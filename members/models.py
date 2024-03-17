from django.db import models
import datetime
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from PIL import Image

def get_admin():
   return User.objects.filter(is_superuser=True).first()

class Family(models.Model):
  name = models.CharField(_('Name'), max_length=72)
  
  parent = models.ForeignKey('self', verbose_name=_('Parent family'), on_delete=models.CASCADE, null=True, blank=True)

  def __str__(self) -> str:
     return self.name
  class Meta:
    verbose_name = _('family')
    verbose_name_plural = _('families')

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


class Member(models.Model):
    account = models.OneToOneField('auth.User', verbose_name=_('Linked Account'), on_delete=models.DO_NOTHING, null=True, blank=True)

    managing_account = models.ForeignKey('auth.User', verbose_name=_('Managing account'), on_delete=models.DO_NOTHING, 
                                      related_name='managing_account', default=1)

    first_name = models.CharField(_('First name'), max_length=128)

    last_name = models.CharField(_('Last name'), max_length=128)

    address = models.ForeignKey(Address, verbose_name=_('Address'), null=True, blank=True, on_delete=models.DO_NOTHING)

    phone = models.CharField(_('Phone'), max_length=32, blank=True)

    birthdate = models.DateField(_('Birthdate'), null=True, blank=True)
    
    email = models.EmailField(_('Email address'), blank=True)

    website = models.URLField(_('Website'), blank=True)

    family = models.ForeignKey(Family, verbose_name=_('Family'), on_delete=models.CASCADE, null=True, blank=True)

    def get_full_name(self):
      uname = f"({self.account.username})" if self.account else ''
      return f"{self.first_name} {self.last_name} {uname}"

    def get_short_name(self):
        return self.first_name if not self.account else self.account.name
    
    def family_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/family_<name>/<filename>
      return "family_{0}/{1}".format(instance.family.name, filename)

    avatar = models.ImageField(default='default.jpg', upload_to=family_directory_path, blank=True)

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

    def save(self, *args, **kwargs):
        # need to have a managing account. If none, use the first admin created
        if self.managing_account is None: self.managing_account = get_admin().id

        # sync back email with linked account email
        if not self.email and self.account and self.account.email :
           self.email = self.account.email
        super().save(*args, **kwargs)

        # resize avatar
        img = Image.open(self.avatar.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.avatar.path)

        # update linked account
        if self.account:
          user = User.objects.get(id=self.account.id)
          user.first_name = self.first_name,
          user.last_name = self.last_name,
          user.email = self.email,
          user.save()

    class Meta:
      verbose_name = _('member')
      verbose_name_plural = _('members')
