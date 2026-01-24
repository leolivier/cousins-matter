from django.shortcuts import render
from django.http import JsonResponse
from django.utils import formats
from django.core.cache import cache
from ..models import Person
from ..utils import register_genealogy_cache

CACHE_KEY_FAMILY_CHART_DATA = "genealogy_family_chart_data"
register_genealogy_cache(CACHE_KEY_FAMILY_CHART_DATA)


def family_chart_view(request, main_person_id=None):
  return render(request, "genealogy/family_chart.html", {"main_person_id": main_person_id})


def family_chart_data(request):
  data = cache.get(CACHE_KEY_FAMILY_CHART_DATA)
  if data is not None:
    return JsonResponse(data, safe=False)

  people = Person.objects.prefetch_related(
    "unions_as_p1",
    "unions_as_p2",
    "unions_as_p1__children",
    "unions_as_p2__children",
    "child_of_family",
    "child_of_family__partner1",
    "child_of_family__partner2",
  ).all()

  data = []
  for person in people:
    # Determine gender for display
    gender = "M" if person.sex == "M" else "F" if person.sex == "F" else "O"

    # Relationships
    rels = {}

    # Parents
    if person.child_of_family:
      father = person.child_of_family.partner1
      mother = person.child_of_family.partner2
      if father:
        rels["father"] = str(father.id)
      if mother:
        rels["mother"] = str(mother.id)

    # Spouses
    spouses = person.get_partners()
    if spouses:
      rels["spouses"] = [str(spouse.id) for spouse in spouses]

    # Children
    children = []
    # Unions where person is partner 1
    for union in person.unions_as_p1.all():
      children.extend([str(child.id) for child in union.children.all()])
    # Unions where person is partner 2
    for union in person.unions_as_p2.all():
      children.extend([str(child.id) for child in union.children.all()])

    if children:
      rels["children"] = list(set(children))  # Remove duplicates if any

    person_data = {
      "id": str(person.id),
      "data": {
        "first name": person.first_name,
        "last name": person.last_name,
        "birthday": formats.date_format(person.birth_date, "SHORT_DATE_FORMAT") if person.birth_date else "",
        "deathday": formats.date_format(person.death_date, "SHORT_DATE_FORMAT") if person.death_date else "",
        "avatar": "",  # Placeholder for avatar
        "gender": gender,
      },
      "rels": rels,
    }

    data.append(person_data)

  cache.set(CACHE_KEY_FAMILY_CHART_DATA, data, 3600)
  return JsonResponse(data, safe=False)
