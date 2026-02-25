import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import formats
from django.core.cache import cache
from django.conf import settings
from ..models import Person, Family
from ..utils import register_genealogy_cache

CACHE_KEY_FAMILY_CHART_DATA = "genealogy_family_chart_data"
register_genealogy_cache(CACHE_KEY_FAMILY_CHART_DATA)


def family_chart_view(request, main_person_id=None):
  return render(request, "genealogy/family_chart.html", {"main_person_id": main_person_id})


def _get_main_person_id(request):
  main_person_id = request.GET.get("main_person_id")
  if not main_person_id:
    main_person_id = getattr(settings, "FAMILY_CHART_ROOT_PERSON_ID", None)

  if not main_person_id:
    first_person = Person.objects.first()
    if first_person:
      main_person_id = first_person.id

  return main_person_id


def _get_bounded_family_graph(main_person_id, max_gen):
  included_ids = set()
  current_level_ids = {int(main_person_id)}

  for _ in range(max_gen + 1):
    if not current_level_ids:
      break
    included_ids.update(current_level_ids)

    parent_families = Family.objects.filter(children__id__in=current_level_ids)
    parent_ids = set()
    for f in parent_families:
      if f.partner1_id:
        parent_ids.add(f.partner1_id)
      if f.partner2_id:
        parent_ids.add(f.partner2_id)

    spouses_as_p1 = Family.objects.filter(partner1_id__in=current_level_ids).values_list("partner2_id", flat=True)
    spouses_as_p2 = Family.objects.filter(partner2_id__in=current_level_ids).values_list("partner1_id", flat=True)

    children_as_p1 = Person.objects.filter(child_of_family__partner1_id__in=current_level_ids).values_list("id", flat=True)
    children_as_p2 = Person.objects.filter(child_of_family__partner2_id__in=current_level_ids).values_list("id", flat=True)

    next_level_ids = parent_ids.union(set(spouses_as_p1), set(spouses_as_p2), set(children_as_p1), set(children_as_p2))
    next_level_ids.discard(None)
    current_level_ids = next_level_ids - included_ids

  # Always include spouses of included_ids to prevent dangling family relations
  spouses_as_p1 = set(Family.objects.filter(partner1_id__in=included_ids).values_list("partner2_id", flat=True))
  spouses_as_p2 = set(Family.objects.filter(partner2_id__in=included_ids).values_list("partner1_id", flat=True))
  included_ids.update(spouses_as_p1)
  included_ids.update(spouses_as_p2)
  included_ids.discard(None)

  return included_ids


def _format_person_data(person, included_ids):
  # Determine gender for display
  gender = "M" if person.sex == "M" else "F" if person.sex == "F" else "O"

  # Relationships
  rels = {}

  # Parents (only if included in the bounded graph)
  if person.child_of_family:
    father = person.child_of_family.partner1
    mother = person.child_of_family.partner2
    if father and father.id in included_ids:
      rels["father"] = str(father.id)
    if mother and mother.id in included_ids:
      rels["mother"] = str(mother.id)

  # Spouses
  spouses = person.get_partners()
  included_spouses = [str(spouse.id) for spouse in spouses if spouse.id in included_ids]
  if included_spouses:
    rels["spouses"] = included_spouses

  # Children
  children = []
  for union in person.unions_as_p1.all():
    children.extend([str(child.id) for child in union.children.all() if child.id in included_ids])
  for union in person.unions_as_p2.all():
    children.extend([str(child.id) for child in union.children.all() if child.id in included_ids])

  if children:
    rels["children"] = list(set(children))

  return {
    "id": str(person.id),
    "data": {
      "first name": person.first_name,
      "last name": person.last_name,
      "birthday": formats.date_format(person.birth_date, "SHORT_DATE_FORMAT") if person.birth_date else "",
      "deathday": formats.date_format(person.death_date, "SHORT_DATE_FORMAT") if person.death_date else "",
      "avatar": "",
      "gender": gender,
    },
    "rels": rels,
  }


def family_chart_data(request):
  main_person_id = _get_main_person_id(request)

  if not main_person_id:
    return JsonResponse([], safe=False)

  # Cache versioning: CACHE_KEY_FAMILY_CHART_DATA stores the current generation UUID.
  # When clear_genealogy_caches is called, it deletes this key, causing a new UUID to be generated,
  # effectively invalidating all specific person caches.
  cache_version = cache.get(CACHE_KEY_FAMILY_CHART_DATA)
  if not cache_version:
    cache_version = str(uuid.uuid4())
    cache.set(CACHE_KEY_FAMILY_CHART_DATA, cache_version, 3600 * 24)

  specific_cache_key = f"{CACHE_KEY_FAMILY_CHART_DATA}_{main_person_id}_{cache_version}"
  data = cache.get(specific_cache_key)
  if data is not None:
    return JsonResponse(data, safe=False)

  # Fetch the bounded graph using BFS
  max_gen = getattr(settings, "FAMILY_CHART_GENERATIONS", 4)
  included_ids = _get_bounded_family_graph(main_person_id, max_gen)

  people = Person.objects.prefetch_related(
    "unions_as_p1",
    "unions_as_p2",
    "unions_as_p1__children",
    "unions_as_p2__children",
    "child_of_family",
    "child_of_family__partner1",
    "child_of_family__partner2",
  ).filter(id__in=included_ids)

  data = [_format_person_data(person, included_ids) for person in people]

  cache.set(specific_cache_key, data, 3600)
  return JsonResponse(data, safe=False)
