from datetime import date, timedelta

from django.conf import settings
from django.db.models import Case, DateField, F, IntegerField, Value, When
from django.db.models.functions import Cast, ExtractDay, ExtractMonth
from django.http import HttpResponse
from django.template.response import TemplateResponse

from ..models import Member
from core.utils import MakeDate


def _birthdays(request, template_name) -> HttpResponse:
  """
  Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
  (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
  """
  today = date.today()
  beg_date = today  # - timedelta(days=1)
  end_date = today + timedelta(days=settings.BIRTHDAY_DAYS)
  current_year = today.year

  members = (
    Member.objects
    .only("id", "first_name", "last_name", "birthdate")
    .filter(is_dead=False)
    .annotate(
      this_year_birthday=Case(
        # Manages only Feb 29th bithdate when the current year is not a leap year
        # i.e. on a non-leap year, a Feb 29th bithdate is considered as a Feb 28th birthdate
        When(
          birthdate__month=2,
          birthdate__day=29,
          then=MakeDate(
            Value(current_year),
            Value(2),
            Value(28 if current_year % 4 != 0 else 29),
          ),
        ),
        default=MakeDate(
          Value(current_year),
          Cast(ExtractMonth(F("birthdate")), output_field=IntegerField()),
          Cast(ExtractDay(F("birthdate")), output_field=IntegerField()),
        ),
        output_field=DateField(),
      )
    )
    .filter(this_year_birthday__range=(beg_date, end_date))
    .order_by("this_year_birthday")
  )

  bdays = []
  for m in members:
    delta = (m.this_year_birthday - today).days
    bdays.append((m, delta))
  context = {"birthdays_list": bdays, "ndays": settings.BIRTHDAY_DAYS}
  # based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
  #  Whitney's and Olivier's (me ;-) comments, replace the standard rendering by a TemplateResponse rendering to allow
  # including this view in the home view
  # return render(request, template_name, context)
  return TemplateResponse(request, template_name, context).render()


def birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays.html")


def include_birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays_include.html")
