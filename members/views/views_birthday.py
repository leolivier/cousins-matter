from datetime import date, timedelta

from django.conf import settings
from django.db.models import DateField, DurationField, ExpressionWrapper, F
from django.db.models.functions import ExtractYear, Now
from django.http import HttpResponse
from django.template.response import TemplateResponse

from ..models import Member


def _birthdays(request, template_name) -> HttpResponse:
  """
  Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
  (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
  """
  today = Now()
  beg_date = today - timedelta(days=1)
  end_date = today + timedelta(days=settings.BIRTHDAY_DAYS)

  members = (
    Member.objects
    .only("id", "first_name", "last_name", "birthdate")
    .filter(is_dead=False)
    # Compute days difference
    # ExtractDoY returns the day of the year (1-365)
    .annotate(
      this_year_birthday=ExpressionWrapper(
        F("birthdate")
        + ExpressionWrapper(
          (ExtractYear(today) - ExtractYear(F("birthdate"))) * timedelta(days=365.25), output_field=DurationField()
        ),
        output_field=DateField(),
      ),
    )
    .filter(this_year_birthday__range=(beg_date, end_date))
    .order_by("this_year_birthday")
  )
  # add days_until_birthday attribute to each member
  today = date.today()
  bdays = []
  for m in members:
    nb = m.this_year_birthday
    # Convert datetime to date if needed
    if hasattr(nb, "date"):
      nb = nb.date()
    delta = nb - today
    bdays.append((m, delta.days))
    print("mmm", m, delta.days)
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
