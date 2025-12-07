from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.db.models.functions import ExtractYear
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.cache import cache
import os
from cm_main.utils import PageOutOfBounds, Paginator
from .models import Person, Family
from .forms import PersonForm, FamilyForm, GedcomImportForm
from .utils import GedcomParser, GedcomExporter


@login_required
def dashboard(request):
    total_people = Person.objects.count()
    total_families = Family.objects.count()
    context = {
        "total_people": total_people,
        "total_families": total_families,
    }
    return render(request, "genealogy/dashboard.html", context)


@login_required
def person_list(request, page_num=1):
    query = request.GET.get("q")
    people = (
        Person.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
        if query
        else Person.objects.all()
    )

    cache_key_suffix = (request.GET.urlencode() or "default") + str(page_num)

    if request.htmx:
        template = "genealogy/person_list.html#person_list_table"
    else:
        template = "genealogy/person_list.html"

    try:
        page = Paginator.get_page(
            request,
            object_list=people,
            page_num=page_num,
            reverse_link="genealogy:person_list_page",
            default_page_size=50,
        )
        return render(
            request, template, {"page": page, "cache_key_suffix": cache_key_suffix}
        )
    except PageOutOfBounds as exc:
        return redirect(exc.redirect_to)


@login_required
def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk)
    return render(request, "genealogy/person_detail.html", {"person": person})


@login_required
def family_tree(request):
    return render(request, "genealogy/family_tree.html")


@login_required
def tree_data(request):
    people_data = []
    for person in Person.objects.all():
        avatar_url = None
        if person.member and person.member.avatar:
            avatar_url = person.member.avatar_mini_url

        people_data.append(
            {
                "id": f"p{person.id}",
                "name": str(person),
                "sex": person.sex,
                "url": f"/genealogy/people/{person.id}/",
                "avatar_url": avatar_url,
                "birth_date": person.birth_date.strftime("%Y")
                if person.birth_date
                else "",
                "death_date": person.death_date.strftime("%Y")
                if person.death_date
                else "",
                "gender_icon": person.gender_icon,
            }
        )

    families_data = []
    for family in Family.objects.all():
        if family.partner1 and family.partner2:
            families_data.append(
                {
                    "id": f"f{family.id}",
                    "partner1_id": f"p{family.partner1.id}",
                    "partner2_id": f"p{family.partner2.id}",
                    "children_ids": [f"p{child.id}" for child in family.children.all()],
                    "union_date": family.union_date.strftime("%Y")
                    if family.union_date
                    else "",
                    "separation_date": family.separation_date.strftime("%Y")
                    if family.separation_date
                    else "",
                }
            )

    return JsonResponse({"people": people_data, "families": families_data})


@login_required
def person_create(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            messages.success(request, _("Person created successfully."))
            clear_genealogy_caches(request)
            return redirect("genealogy:person_detail", pk=person.pk)
    else:
        form = PersonForm()
    return render(
        request, "genealogy/person_form.html", {"form": form, "title": _("Add Person")}
    )


@login_required
def person_update(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == "POST":
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, _("Person updated successfully."))
            clear_genealogy_caches(request)
            return redirect("genealogy:person_detail", pk=person.pk)
    else:
        form = PersonForm(instance=person)
    return render(
        request, "genealogy/person_form.html", {"form": form, "title": _("Edit Person")}
    )


@login_required
def person_delete(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == "POST":
        person.delete()
        messages.success(request, _("Person deleted successfully."))
        clear_genealogy_caches(request)
        return redirect("genealogy:person_list")
    return render(request, "genealogy/person_confirm_delete.html", {"person": person})


@login_required
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
        return render(
            request, template, {"page": page, "cache_key_suffix": cache_key_suffix}
        )
    except PageOutOfBounds as exc:
        return redirect(exc.redirect_to)


@login_required
def family_create(request):
    if request.method == "POST":
        form = FamilyForm(request.POST)
        if form.is_valid():
            # family =
            form.save()
            messages.success(request, _("Family created successfully."))
            clear_genealogy_caches(request)
            return redirect("genealogy:dashboard")  # Or family detail if we had one
    else:
        form = FamilyForm()
    return render(
        request, "genealogy/family_form.html", {"form": form, "title": _("Add Family")}
    )


@login_required
def family_update(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == "POST":
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, _("Family updated successfully."))
            clear_genealogy_caches(request)
            return redirect("genealogy:dashboard")
    else:
        form = FamilyForm(instance=family)
    return render(
        request, "genealogy/family_form.html", {"form": form, "title": _("Edit Family")}
    )


@login_required
def family_delete(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == "POST":
        family.delete()
        messages.success(request, _("Family deleted successfully."))
        clear_genealogy_caches(request)
        return redirect("genealogy:dashboard")
    return render(request, "genealogy/family_confirm_delete.html", {"family": family})


@login_required
def import_gedcom(request):
    if request.method == "POST":
        form = GedcomImportForm(request.POST, request.FILES)
        if form.is_valid():
            gedcom_file = request.FILES["gedcom_file"]
            # Save temporary file
            path = default_storage.save(
                "tmp/" + gedcom_file.name, ContentFile(gedcom_file.read())
            )
            full_path = os.path.join(default_storage.location, path)

            try:
                parser = GedcomParser(full_path)
                parser.parse()
                messages.success(request, _("GEDCOM imported successfully."))
                clear_genealogy_caches(request)
            except Exception as e:
                messages.error(
                    request, _("Error importing GEDCOM: %(error)s") % {"error": str(e)}
                )
            finally:
                default_storage.delete(path)

            return redirect("genealogy:dashboard")
    else:
        form = GedcomImportForm()
    return render(request, "genealogy/import_gedcom.html", {"form": form})


@login_required
def export_gedcom(request):
    exporter = GedcomExporter()
    gedcom_content = exporter.export()
    response = HttpResponse(gedcom_content, content_type="text/gedcom")
    response["Content-Disposition"] = 'attachment; filename="genealogy.ged"'
    return response


@login_required
def statistics(request):
    # Gender Distribution
    gender_data = Person.objects.values("sex").annotate(count=Count("sex"))

    # Top Names
    top_first_names = (
        Person.objects.values("first_name")
        .annotate(count=Count("first_name"))
        .order_by("-count")[:10]
    )
    top_last_names = (
        Person.objects.values("last_name")
        .annotate(count=Count("last_name"))
        .order_by("-count")[:10]
    )

    # Births per Decade
    birth_years = (
        Person.objects.filter(birth_date__isnull=False)
        .annotate(year=ExtractYear("birth_date"))
        .values("year")
    )
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


def clear_genealogy_caches(request):
    cache.delete("genealogy_statistics")
    cache.delete("genealogy_family_tree")
    cache.delete("genealogy_person_list")
    cache.delete("genealogy_family_list")


@login_required
def refresh(request):
    clear_genealogy_caches(request)
    messages.success(request, _("Genealogy data refreshed successfully."))
    return redirect(request.META.get("HTTP_REFERER"))
