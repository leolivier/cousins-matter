from django.http import HttpResponse
from django.shortcuts import render
from datetime import date, timedelta
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from ..models import Member
from cousinsmatter import settings

def _birthdays(request, template_name) -> HttpResponse:
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
  # template_name = "members/birthdays.html"
  # return render(request, template_name, context)
  return TemplateResponse(request, template_name, context).render()

@login_required
def birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/birthdays.html")

@login_required
def include_birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/birthdays_include.html")