from django.http import HttpResponse
from datetime import date, timedelta
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from ..models import Member
from cousinsmatter import settings

from typing import Any
from django.db.models.query import QuerySet
from django.contrib.auth.mixins import LoginRequiredMixin

from django.views import generic
from ..models import birthdays_F, birthdays_raw

class BirthdaysView(LoginRequiredMixin, generic.ListView):
  """
  Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
  (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
  """
  def __init__(self, template_name="members/birthdays.html"):
    self.template_name = template_name

  def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
    return {
      "birthdays_list": birthdays_raw(settings.BIRTHDAY_DAYS),
      "ndays" : settings.BIRTHDAY_DAYS
    }
  
  def get(self, request):
  # based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
  #  Whitney's and Olivier's (me ;-) comments, replace the standard rendering by a TemplateResponse rendering to allow
  # including this view in the home view
    context=self.get_context_data()
    print(context)
    return TemplateResponse(request, self.template_name, context).render()


@login_required
def include_birthdays(request) -> HttpResponse:
  view = BirthdaysView(template_name="members/birthdays_include.html").as_view()
  return view.get(request)
