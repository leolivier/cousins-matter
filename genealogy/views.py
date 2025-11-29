from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.db.models.functions import ExtractYear
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .models import Person, Family
from .forms import PersonForm, FamilyForm, GedcomImportForm
from .utils import GedcomParser, GedcomExporter


def dashboard(request):
    total_people = Person.objects.count()
    total_families = Family.objects.count()
    context = {
        "total_people": total_people,
        "total_families": total_families,
    }
    return render(request, "genealogy/dashboard.html", context)


def person_list(request):
    query = request.GET.get("q")
    if query:
        people = Person.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
    else:
        people = Person.objects.all()

    if request.htmx:
        template = "genealogy/person_list.html#person-table-body"
    else:
        template = "genealogy/person_list.html"

    return render(request, template, {"people": people})


def person_detail(request, pk):
    person = get_object_or_404(Person, pk=pk)
    return render(request, "genealogy/person_detail.html", {"person": person})


def family_tree(request):
    return render(request, "genealogy/family_tree.html")


def tree_data(request):
    nodes = []
    links = []

    # Add all people as nodes
    for person in Person.objects.all():
        nodes.append(
            {
                "id": f"p{person.id}",
                "name": str(person),
                "type": "person",
                "sex": person.sex,
                "url": f"/genealogy/people/{person.id}/",
            }
        )

        # Add link to parents (via family)
        if person.child_of_family:
            # We can link person to their parents directly or to a "family" node
            # For a force graph, linking to parents is often clearer
            if person.child_of_family.partner1:
                links.append(
                    {
                        "source": f"p{person.child_of_family.partner1.id}",
                        "target": f"p{person.id}",
                        "type": "parent",
                    }
                )
            if person.child_of_family.partner2:
                links.append(
                    {
                        "source": f"p{person.child_of_family.partner2.id}",
                        "target": f"p{person.id}",
                        "type": "parent",
                    }
                )

    # Add partner links
    for family in Family.objects.all():
        if family.partner1 and family.partner2:
            links.append(
                {
                    "source": f"p{family.partner1.id}",
                    "target": f"p{family.partner2.id}",
                    "type": "partner",
                }
            )

    return JsonResponse({"nodes": nodes, "links": links})


def person_create(request):
    if request.method == "POST":
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            messages.success(request, _("Person created successfully."))
            return redirect("genealogy:person_detail", pk=person.pk)
    else:
        form = PersonForm()
    return render(
        request, "genealogy/person_form.html", {"form": form, "title": _("Add Person")}
    )


def person_update(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == "POST":
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            form.save()
            messages.success(request, _("Person updated successfully."))
            return redirect("genealogy:person_detail", pk=person.pk)
    else:
        form = PersonForm(instance=person)
    return render(
        request, "genealogy/person_form.html", {"form": form, "title": _("Edit Person")}
    )


def person_delete(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == "POST":
        person.delete()
        messages.success(request, _("Person deleted successfully."))
        return redirect("genealogy:person_list")
    return render(request, "genealogy/person_confirm_delete.html", {"person": person})


def family_list(request):
    families = Family.objects.all()
    return render(request, "genealogy/family_list.html", {"families": families})


def family_create(request):
    if request.method == "POST":
        form = FamilyForm(request.POST)
        if form.is_valid():
            # family =
            form.save()
            messages.success(request, _("Family created successfully."))
            return redirect("genealogy:dashboard")  # Or family detail if we had one
    else:
        form = FamilyForm()
    return render(
        request, "genealogy/family_form.html", {"form": form, "title": _("Add Family")}
    )


def family_update(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == "POST":
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            form.save()
            messages.success(request, _("Family updated successfully."))
            return redirect("genealogy:dashboard")
    else:
        form = FamilyForm(instance=family)
    return render(
        request, "genealogy/family_form.html", {"form": form, "title": _("Edit Family")}
    )


def family_delete(request, pk):
    family = get_object_or_404(Family, pk=pk)
    if request.method == "POST":
        family.delete()
        messages.success(request, _("Family deleted successfully."))
        return redirect("genealogy:dashboard")
    return render(request, "genealogy/family_confirm_delete.html", {"family": family})


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


def export_gedcom(request):
    exporter = GedcomExporter()
    gedcom_content = exporter.export()
    response = HttpResponse(gedcom_content, content_type="text/gedcom")
    response["Content-Disposition"] = 'attachment; filename="genealogy.ged"'
    return response


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
