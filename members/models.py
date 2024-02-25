from django.db import models
import datetime
from django.utils.translation import gettext_lazy as _

class Family(models.Model):
  name = models.CharField(_('Name'), max_length=72)
  
  parent = models.ForeignKey('self', verbose_name=_('Parent family'), on_delete=models.CASCADE)

class Address(models.Model):
  street_number = models.CharField(_('Street number'), max_length=12)
  
  street = models.CharField(_('Street name'), max_length=120)

  complementary_info = models.CharField(_('Complementary info'), max_length=120)

  zip_code = models.CharField(_('Zip code'), max_length=12)

  city = models.CharField(_('City'), max_length=120)

  country = models.CharField(_('Country'), max_length=32)

  def __str__(self) -> str:
    return f"""
{self.street_number}, {self.street}
{self.complementary_info}
{self.zip_code}, {self.city}
{self.country}
"""

class Member(models.Model):
    first_name = models.CharField(_('First name'), max_length=128)

    last_name = models.CharField(_('Last name'), max_length=128)

    address = models.ForeignKey(Address, verbose_name=_('Address'), null=True, blank=True, on_delete=models.DO_NOTHING)

    cell_phone = models.CharField(_('Cell phone'), max_length=32, blank=True)

    alternate_phone = models.CharField(_('Alternate phone'), max_length=32, blank=True)

    birthdate = models.DateField(_('Birthdate'), )
    
    personal_email = models.EmailField(_('Personal email'), blank=True)

    alternate_email = models.EmailField(_('Alternate email'), blank=True)

    website = models.URLField(_('Website'), blank=True)

    family = models.ForeignKey(Family, verbose_name=_('Family'), on_delete=models.CASCADE, null=True, blank=True)

    def family_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/family_<name>/<filename>
      return "family_{0}/{1}".format(instance.family.name, filename)

    avatar = models.ImageField(upload_to=family_directory_path, blank=True)

    def __str__(self) -> str:
      return f"{self.first_name} {self.last_name}"

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




