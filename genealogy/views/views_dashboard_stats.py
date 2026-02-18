from django.shortcuts import render, redirect
from django.db.models import Count
from django.db.models.functions import ExtractYear
from django.contrib import messages
from django.utils.translation import gettext as _
from ..models import Person, Family
from ..utils import clear_genealogy_caches, register_genealogy_cache

register_genealogy_cache("genealogy_statistics")


def dashboard(request):
  total_people = Person.objects.count()
  total_families = Family.objects.count()
  context = {
    "total_people": total_people,
    "total_families": total_families,
  }
  return render(request, "genealogy/dashboard.html", context)


def statistics(request):
  # Gender Distribution
  gender_data = Person.objects.values("sex").annotate(count=Count("sex"))

  # Top Names
  top_first_names = Person.objects.values("first_name").annotate(count=Count("first_name")).order_by("-count")[:10]
  top_last_names = Person.objects.values("last_name").annotate(count=Count("last_name")).order_by("-count")[:10]

  # Births per Decade
  birth_years = Person.objects.filter(birth_date__isnull=False).annotate(year=ExtractYear("birth_date")).values("year")
  decades = {}
  for entry in birth_years:
    decade = (entry["year"] // 10) * 10
    decades[decade] = decades.get(decade, 0) + 1

  sorted_decades = dict(sorted(decades.items()))

  context = {
    "gender_data": list(gender_data),
    "top_first_names": list(top_first_names),
    "top_last_names": list(top_last_names),
    "decades": list(sorted_decades.keys()),
    "births_per_decade": list(sorted_decades.values()),
  }
  return render(request, "genealogy/statistics.html", context)


def refresh(request):
  clear_genealogy_caches()
  messages.success(request, _("Genealogy data refreshed successfully."))
  return redirect(request.META.get("HTTP_REFERER"))
