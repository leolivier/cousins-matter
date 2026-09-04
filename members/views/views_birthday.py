from django.http import HttpResponse
from django.template.response import TemplateResponse

from tenants.settings_overrides import tenant_setting
from ..services.members import get_birthdays


def _birthdays(request, template_name) -> HttpResponse:
  """
  Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
  (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
  """
  ndays = tenant_setting("birthday_days")
  birthdays = get_birthdays(ndays)
  context = {"birthdays_list": birthdays, "ndays": ndays}
  # based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
  #  Whitney's and Olivier's (me ;-) comments, replace the standard rendering by a TemplateResponse rendering to allow
  # including this view in the home view
  # return render(request, template_name, context)
  return TemplateResponse(request, template_name, context).render()


def birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays.html")


def include_birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays_include.html")
