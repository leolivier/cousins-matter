from django.http import HttpResponse
from django.shortcuts import render
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from ..models import Member
from cousinsmatter import settings

@login_required
def birthdays(request) -> HttpResponse:
  """
  Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
  (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
  """
  today = date.today()
  deltaNdays = timedelta(days = settings.BIRTHDAY_DAYS)
  bdays = []
  for m in Member.objects.all():
    nb = m.next_birthday()
    delta = nb - today
    if delta < deltaNdays:
        bdays.append((m, delta.days))
  context = {
    "birthdays_list": bdays,
    "ndays": settings.BIRTHDAY_DAYS
  }
  return render(request, "members/birthdays.html", context)
