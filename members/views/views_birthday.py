from django.http import HttpResponse
from datetime import date, timedelta
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, IntegerField, DateField, Case, CharField, When, Q
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear, Cast
from django.conf import settings

from ..models import Member


def _birthdays(request, template_name) -> HttpResponse:
    """
    Return the members with their birthday in the next settings.BIRTHDAY_DAYS days
    (or previous settings.BIRTHDAY_DAYS days if settings.BIRTHDAY_DAYS <0)
    """
    today = date.today()
    deltaNdays = timedelta(days=settings.BIRTHDAY_DAYS)
    end_date = today + deltaNdays

    # Compute year of next birthday
    next_birthday_year = ExpressionWrapper(
        Case(
            When(
                Q(birthdate__month__gt=F('current_month')) |
                (Q(birthdate__month=F('current_month')) & Q(birthdate__day__gt=F('current_day'))),
                then=F('current_year')
            ),
            default=F('current_year') + 1,
            output_field=IntegerField()
        ),
        output_field=IntegerField()
    )

    # Compute netx birthday date
    next_birthday = ExpressionWrapper(
        Cast(next_birthday_year, output_field=CharField()) + '-' +
        Cast(ExtractMonth('birthdate'), output_field=CharField()) + '-' +
        Cast(ExtractDay('birthdate'), output_field=CharField()),
        output_field=DateField()
    )

    # Calculer le nombre de jours jusqu'au prochain anniversaire
    days_until_birthday = ExpressionWrapper(
        next_birthday - today,
        output_field=IntegerField()
    )

    # Requête avec annotations et filtres
    members = Member.objects.annotate(
        current_year=ExtractYear(today),
        current_month=ExtractMonth(today),
        current_day=ExtractDay(today),
        next_birthday=next_birthday,
        days_until_birthday=days_until_birthday
    ).filter(
        next_birthday__range=(today, end_date)
    ).order_by('days_until_birthday')

    print(members.query)
    
    # Retourner les résultats au format attendu
    context = {
     "birthdays_list": members,
     "ndays": settings.BIRTHDAY_DAYS
    }

    # based on https://stackoverflow.com/questions/17178525/django-how-to-include-a-view-from-within-a-template#56476932
    #  Whitney's and Olivier's (me ;-) comments, replace the standard rendering by a TemplateResponse rendering to allow
    # including this view in the home view
    # return render(request, template_name, context)
    return TemplateResponse(request, template_name, context).render()


@login_required
def birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays.html")


@login_required
def include_birthdays(request) -> HttpResponse:
  return _birthdays(request, "members/members/birthdays_include.html")
