from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext as _
from cm_main.utils import PageOutOfBounds, Paginator
from ..models import Family
from ..forms import FamilyForm
from ..utils import clear_genealogy_caches


def family_list(request, page_num=1):
  query = request.GET.get("q")
  if query:
    families = Family.objects.filter(
      Q(partner1__first_name__icontains=query)
      | Q(partner2__first_name__icontains=query)
      | Q(partner1__last_name__icontains=query)
      | Q(partner2__last_name__icontains=query)
    )
  else:
    families = Family.objects.all()

  cache_key_suffix = (request.GET.urlencode() or "default") + str(page_num)

  if request.htmx:
    template = "genealogy/family_list.html#family_list_table"
  else:
    template = "genealogy/family_list.html"

  try:
    page = Paginator.get_page(
      request,
      object_list=families,
      page_num=page_num,
      reverse_link="genealogy:family_list_page",
      default_page_size=25,
    )
    return render(request, template, {"page": page, "cache_key_suffix": cache_key_suffix})
  except PageOutOfBounds as exc:
    return redirect(exc.redirect_to)


def family_create(request):
  if request.method == "POST":
    form = FamilyForm(request.POST)
    if form.is_valid():
      # family =
      form.save()
      messages.success(request, _("Family created successfully."))
      clear_genealogy_caches()
      return redirect("genealogy:dashboard")  # Or family detail if we had one
  else:
    form = FamilyForm()
  return render(request, "genealogy/family_form.html", {"form": form, "title": _("Add Family")})


def family_update(request, pk):
  family = get_object_or_404(Family, pk=pk)
  if request.method == "POST":
    form = FamilyForm(request.POST, instance=family)
    if form.is_valid():
      form.save()
      messages.success(request, _("Family updated successfully."))
      clear_genealogy_caches()
      return redirect("genealogy:dashboard")
  else:
    form = FamilyForm(instance=family)
  return render(request, "genealogy/family_form.html", {"form": form, "title": _("Edit Family")})


def family_delete(request, pk):
  family = get_object_or_404(Family, pk=pk)
  if request.method == "POST":
    family.delete()
    messages.success(request, _("Family deleted successfully."))
    clear_genealogy_caches()
    return redirect("genealogy:dashboard")
  return render(request, "genealogy/family_confirm_delete.html", {"family": family})
