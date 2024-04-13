from django.db import models
import datetime
from PIL import Image, ImageOps
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
import logging
from cousinsmatter import settings

logger = logging.getLogger(__name__)

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
    ordering = ['name']

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


class Member(models.Model):
    account = models.OneToOneField('auth.User', verbose_name=_('Linked Account'), on_delete=models.CASCADE)

    managing_account = models.ForeignKey('auth.User', verbose_name=_('Managing account'), on_delete=models.CASCADE, 
                                      related_name='managing_account', default=1)
    # TODO: fix the avatar path is not sent by the form which always provide default.jpg...
    avatar = models.ImageField(default='default.jpg', upload_to=settings.AVATARS_DIR, blank=True)

    address = models.ForeignKey(Address, verbose_name=_('Address'), null=True, blank=True, on_delete=models.DO_NOTHING)

    phone = models.CharField(_('Phone'), max_length=32, blank=True)

    birthdate = models.DateField(_('Birthdate'), null=True, blank=False)
    
    website = models.URLField(_('Website'), blank=True)

    family = models.ForeignKey(Family, verbose_name=_('Family'), on_delete=models.CASCADE, null=True, blank=True)

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

    class Meta:
      verbose_name = _('member')
      verbose_name_plural = _('members')
      ordering = ['account__last_name', 'account__first_name']

from django.db.models.functions import (ExtractDay, ExtractMonth, ExtractYear, Now, Concat, TruncYear)
from django.db.models.expressions import Func, Case, When, Expression, Value as V, ExpressionWrapper
from django.db.models import CharField, DateField, IntegerField, Q, F

sql_statement="""
with precalc(id, birthdate, diff, birthday_year) as (
	select 
    members_member.id as id, 
    members_member.birthdate as birthdate,
		(julianday(substr(current_date, 1, 4) || substr(birthdate, -6, 6)) - julianday(current_date)) as diff,
		case
			when (substr(current_date, 6, 2)>substr(birthdate, 6, 2) or (substr(current_date, 6, 2)=substr(birthdate, 6, 2) and substr(current_date, -2, 2)>substr(birthdate, -2, 2)))
			then substr(current_date, 1, 4) + 1
			else substr(current_date, 1, 4) 
		end  as birthday_year
	from members_member)
select precalc.id, birthdate,
  account.first_name, account.last_name, 
	case 
		when(precalc.diff >= 0)
		then precalc.diff
		else precalc.diff + strftime("%j", substr(current_date, 1, 4)||'-12-31')
	end as delta,
	precalc.birthday_year || substr(birthdate, -6, 6) as next_birthday,
	case 
		when(precalc.diff >= 0)
		then substr(current_date, 1, 4)-substr(birthdate, 1, 4)
		else substr(current_date, 1, 4)-substr(birthdate, 1, 4) + 1
	end as age
from precalc INNER JOIN auth_user as account ON (precalc.id = account.id) 
where delta < 100 
order by delta;
"""
class Date(Func):
  function = 'date'
  template = "%(function)s(%(expressions)s, 'localtime')"
  def __init__(self, year, month, day, **extra):
    lst=[]
    for attribute in [year, month, day]:
      if not isinstance(attribute, int) and not isinstance(attribute, Expression) and not isinstance(attribute, F):
        raise ValueError(f'Date() must be called with year, month and day as integers or Expressions or F: {attribute} is a {type(attribute)}')
      if isinstance(attribute, int):
        attribute=V(attribute)
      lst.append(attribute)
    
    date=Concat(lst[0], V('-'), lst[1], V('-'), lst[2], output_field=CharField())
    expressions = [date]
    super().__init__(*expressions, **extra)

class JulianDay(Func):
  function = 'julianday'
  template = "%(function)s(%(expressions)s)"

class GetYear(Func):
  function = 'substr'
  template = "%(function)s(%(expressions)s, 1, 4)"

class GetMonth(Func):
  function = 'substr'
  template = "%(function)s(%(expressions)s, 6, 2)"

class GetDay(Func):
  function = 'substr'
  template = "%(function)s(%(expressions)s, 9, 2)"

def birthdays_raw(ndays: int):
  res = Member.objects.raw(sql_statement)
  print(res)
  return res;



def birthdays_F(ndays:int):
  today = datetime.date.today()
  year = today.year
  month = today.month
  day = today.day
  deltaNdays = datetime.timedelta(days = ndays)
# values('id', 'account__first_name', 'account__last_name').
  f = Member.objects.annotate(
        cur_month=V(month),
        cur_day=V(day),
        birth_year=ExtractYear('birthdate'),
        birth_month=ExtractMonth('birthdate'),
        birth_day=ExtractDay('birthdate'),
        next_birthday_year=Case(
          When(Q(cur_month__gt=F('birth_month')) | 
              (Q(cur_month=F('birth_month')) & Q(cur_day__gt=F('birth_day'))), 
              then=V(year + 1)),
          default=V(year)
        ),
        next_birthday=Date(F('next_birthday_year'), month, day),
        age=F('next_birthday_year')-F('birth_year'),
        # age=Case(
        #   When(next_birthday=TruncDay(Now()), 
        #        then=ExpressionWrapper(ExtractYear(Now(), output_field=IntegerField()) -
        #                               ExtractYear('next_birthday', output_field=IntegerField()), 
        #                               output_field=IntegerField())),
        #   defaut=ExpressionWrapper(ExtractYear(Now(), output_field=IntegerField()) -
        #                            ExtractYear('next_birthday', output_field=IntegerField())-1, 
        #                            output_field=IntegerField())
        # ),
        when=(JulianDay('next_birthday', output_field=IntegerField()) - JulianDay(Now(), output_field=IntegerField()))
  ) #.filter(when__lt=V(deltaNdays)).order_by('when')

  print (f"birthdays query={f.query}")
  return f