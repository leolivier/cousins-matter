from django.conf import settings
from django.http import HttpResponse
from django.template.response import TemplateResponse

from ..services.members import get_birthdays


def _birthdays(request, template_name) -> HttpResponse:
  """
  Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
  (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
  """
  birthdays = get_birthdays(settings.BIRTHDAY_DAYS)
  context = {"birthdays_list": birthdays, "ndays": settings.BIRTHDAY_DAYS}
  # based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
  #  Whitney's and Olivier's (me ;-) comments, replace the standard rendering by a TemplateResponse rendering to allow
  # including this view in the home view
  # return render(request, template_name, context)
  return TemplateResponse(request, template_name, context).render()


def birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays.html")


def include_birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays_include.html")
