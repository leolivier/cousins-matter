from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from core.utils import PageOutOfBounds, Paginator

from ..forms import PersonForm
from ..models import Person
from ..services import PERSON_SORT_FIELDS, get_people_queryset
from ..utils import clear_genealogy_caches


def person_list(request, page_num=1):
  query = request.GET.get("q")
  # Normalize sort for both the template context and the service call; the service
  # re-validates defensively. PERSON_SORT_FIELDS guards against order_by injection.
  sort = request.GET.get("sort") or "name"
  if sort not in PERSON_SORT_FIELDS:
    sort = "name"
  direction = "desc" if request.GET.get("dir") == "desc" else "asc"

  people = get_people_queryset(query, sort, direction)

  cache_key_suffix = (request.GET.urlencode() or "default") + str(page_num)

  template = "genealogy/person_list.html"
  if request.htmx:
    template += "#person_list_table"

  try:
    page = Paginator.get_page(
      request,
      object_list=people,
      page_num=page_num,
      reverse_link="genealogy:person_list_page",
      default_page_size=50,
    )
    return render(
      request,
      template,
      {"page": page, "cache_key_suffix": cache_key_suffix, "sort": sort, "dir": direction},
    )
  except PageOutOfBounds as exc:
    return redirect(exc.redirect_to)


def person_detail(request, pk):
  person = get_object_or_404(
    Person.objects.select_related(
      "child_of_family", "child_of_family__partner1", "child_of_family__partner2", "member"
    ).prefetch_related("unions_as_p1__partner2", "unions_as_p1__children", "unions_as_p2__partner1", "unions_as_p2__children"),
    pk=pk,
  )
  return render(request, "genealogy/person_detail.html", {"person": person})


def person_create(request):
  if request.method == "POST":
    form = PersonForm(request.POST)
    if form.is_valid():
      person = form.save()
      messages.success(request, _("Person created successfully."))
      clear_genealogy_caches()
      return redirect("genealogy:person_detail", pk=person.pk)
  else:
    form = PersonForm()
  return render(request, "genealogy/person_form.html", {"form": form, "title": _("Add Person")})


def person_update(request, pk):
  person = get_object_or_404(Person, pk=pk)
  if request.method == "POST":
    form = PersonForm(request.POST, instance=person)
    if form.is_valid():
      form.save()
      messages.success(request, _("Person updated successfully."))
      clear_genealogy_caches()
      return redirect("genealogy:person_detail", pk=person.pk)
  else:
    form = PersonForm(instance=person)
  return render(request, "genealogy/person_form.html", {"form": form, "title": _("Edit Person")})


def person_delete(request, pk):
  person = get_object_or_404(Person, pk=pk)
  if request.method == "POST":
    person.delete()
    messages.success(request, _("Person deleted successfully."))
    clear_genealogy_caches()
    return redirect("genealogy:person_list")
  return render(request, "genealogy/person_confirm_delete.html", {"person": person})
