from django.http import HttpResponse
from django.shortcuts import render
from datetime import date, timedelta
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from ..models import Member
from django.conf import settings

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
  ordered_bdays = sorted(bdays, key=lambda x: x[1])
  context = {
    "birthdays_list": ordered_bdays,
    "ndays": settings.BIRTHDAY_DAYS
  }
  # based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
  #  Whitney's and Olivier's (me ;-) comments, replace the standard rendering by a TemplateResponse rendering to allow
  # including this view in the home view
  # return render(request, template_name, context)
  return TemplateResponse(request, template_name, context).render()

@login_required
def birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/birthdays.html")

@login_required
def include_birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/birthdays_include.html")