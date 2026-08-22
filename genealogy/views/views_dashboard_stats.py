from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _

from ..models import Family, Person
from ..services import build_statistics_context
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
  return render(request, "genealogy/statistics.html", build_statistics_context())


def refresh(request):
  clear_genealogy_caches()
  messages.success(request, _("Genealogy data refreshed successfully."))
  referer = request.META.get("HTTP_REFERER")
  if referer and url_has_allowed_host_and_scheme(referer, {request.get_host()}, request.is_secure()):
    return redirect(referer)
  return redirect("genealogy:dashboard")
