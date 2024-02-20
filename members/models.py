from django.db import models
from django.utils import timezone
import datetime

class Family(models.Model):
  name = models.CharField(max_length=72)
  
  parent = models.ForeignKey('self', on_delete=models.CASCADE)

class Address(models.Model):
  street_number = models.CharField(max_length=12)
  
  street = models.CharField(max_length=120)

  complementary_info = models.CharField(max_length=120)

  zip_code = models.CharField(max_length=12)

  city = models.CharField(max_length=120)

  country = models.CharField(max_length=32)

  def __str__(self) -> str:
    return f"""
{self.street_number}, {self.street}
{self.complementary_info}
{self.zip_code}, {self.city}
{self.country}
"""

class Member(models.Model):
    first_name = models.CharField(max_length=128)

    last_name = models.CharField(max_length=128)

    address = models.ForeignKey(Address, null=True, blank=True, on_delete=models.DO_NOTHING)

    cell_phone = models.CharField(max_length=32, blank=True)

    alternate_phone = models.CharField(max_length=32, blank=True)

    birthdate = models.DateField()
    
    personal_email = models.EmailField(blank=True)

    alternate_email = models.EmailField(blank=True)

    website = models.URLField(blank=True)

    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)

    def family_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/family_<name>/<filename>
      return "family_{0}/{1}".format(instance.family.name, filename)

    avatar = models.ImageField(upload_to=family_directory_path, blank=True)

    def __str__(self) -> str:
      return f"{self.first_name} {self.last_name}"

    def birthday(self) -> str:
      """TODO use locale for D/M order"""
      return self.birthdate.strftime('%d/%m')
    
    def next_birthday(self) -> datetime.date:
      today = datetime.datetime.today()
      year = today.year
      if today.month > self.birthdate.month or \
         (today.month == self.birthdate.month and today.day > self.birthdate.day):
            year += 1
      return self.birthdate.replace(year=year)
      
    def age(self) -> int:
      today = datetime.datetime.today()
      years = today.year - self.birthdate.year
      return years if (today >= self.next_birthday()) else years-1
      
    @staticmethod
    def next_birthdays(ndays):
      today = datetime.date.today()
      delta = datetime.timedelta(days = ndays)
      bdates = []
      for m in Member.objects.all():
        if m.next_birthday() <= today + delta:
          bdates.append(m)
      return bdates
    



