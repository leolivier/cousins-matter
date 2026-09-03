from itertools import chain

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from django.utils import formats
from django.utils.translation import gettext as _

from .models import Family, Person
from .utils import GedcomParser, clear_genealogy_caches

# --------------------------------------------------------------------------------------
# dashboard / statistics
# --------------------------------------------------------------------------------------


def build_statistics_context():
  """Aggregate genealogy stats for the statistics page: gender distribution,
  top first/last names, and births per decade."""
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

  return {
    "gender_data": list(gender_data),
    "top_first_names": list(top_first_names),
    "top_last_names": list(top_last_names),
    "decades": list(sorted_decades.keys()),
    "births_per_decade": list(sorted_decades.values()),
  }


# --------------------------------------------------------------------------------------
# family chart
# --------------------------------------------------------------------------------------


def resolve_main_person_id(explicit_id):
  """Resolve which person to center the family chart on: the explicitly
  requested id, the configured root person (FAMILY_CHART_ROOT_PERSON_ID), or
  the first person in the DB. Returns None when there is nobody to chart."""
  if explicit_id:
    return explicit_id
  configured = getattr(settings, "FAMILY_CHART_ROOT_PERSON_ID", None)
  if configured:
    return configured
  first_person = Person.objects.first()
  return first_person.id if first_person else None


def _get_bounded_family_graph(main_person_id, max_gen):
  included_ids = set()
  current_level_ids = {int(main_person_id)}

  for _generation in range(max_gen + 1):
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


def _gender_code(person):
  return "M" if person.sex == "M" else "F" if person.sex == "F" else "O"


def _person_brief(person):
  """Compact, JSON-serializable summary of a related person, for the hover tooltip."""
  return {
    "id": str(person.id),
    "name": f"{person.first_name} {person.last_name}",
    "birth": formats.date_format(person.birth_date, "SHORT_DATE_FORMAT") if person.birth_date else "",
    "death": formats.date_format(person.death_date, "SHORT_DATE_FORMAT") if person.death_date else "",
    "gender": _gender_code(person),
  }


def _format_person_data(person, included_ids):
  # Determine gender for display
  gender = _gender_code(person)

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

  # --- Tooltip data (independent of the bounded graph, for the hover popover) ---
  return {
    "id": str(person.id),
    "data": {
      "first name": person.first_name,
      "last name": person.last_name,
      "birthday": formats.date_format(person.birth_date, "SHORT_DATE_FORMAT") if person.birth_date else "",
      "deathday": formats.date_format(person.death_date, "SHORT_DATE_FORMAT") if person.death_date else "",
      "avatar": "",
      "gender": gender,
      # Person.age already returns age at death (if deceased) or current age (if living).
      "age": person.age,
      "birth_place": person.birth_place or "",
      "death_place": person.death_place or "",
      "parents": _tooltip_parents(person),
      "children": _tooltip_children(person),
      "marriages": _tooltip_marriages(person),
    },
    "rels": rels,
  }


def _tooltip_parents(person):
  """Parents of a person, for the hover tooltip (regardless of chart bounds)."""
  parents = []
  if person.child_of_family:
    if person.child_of_family.partner1:
      parents.append(_person_brief(person.child_of_family.partner1))
    if person.child_of_family.partner2:
      parents.append(_person_brief(person.child_of_family.partner2))
  return parents


def _tooltip_children(person):
  """Children of a person (deduplicated by id), for the hover tooltip."""
  children_by_id = {}
  for union in chain(person.unions_as_p1.all(), person.unions_as_p2.all()):
    for child in union.children.all():
      children_by_id[str(child.id)] = _person_brief(child)
  return list(children_by_id.values())


def _tooltip_marriages(person):
  """Unions of a person (spouse + date/place/type), for the hover tooltip."""
  marriages = []
  for union in chain(person.unions_as_p1.all(), person.unions_as_p2.all()):
    spouse = union.partner2 if union.partner1_id == person.id else union.partner1
    marriages.append({
      "spouse": _person_brief(spouse) if spouse else None,
      "date": formats.date_format(union.union_date, "SHORT_DATE_FORMAT") if union.union_date else "",
      "place": union.union_place or "",
      # str() is required: get_union_type_display() returns a lazy proxy that
      # JsonResponse/json.dumps cannot serialize.
      "type": str(union.get_union_type_display()),
    })
  return marriages


def build_family_chart_data(main_person_id):
  """Compute the family-chart payload for ``main_person_id``: the bounded graph
  of relatives (up to FAMILY_CHART_GENERATIONS) and each person's display +
  relationship data for the chart and hover tooltips."""
  max_gen = getattr(settings, "FAMILY_CHART_GENERATIONS", 4)
  included_ids = _get_bounded_family_graph(main_person_id, max_gen)

  people = Person.objects.prefetch_related(
    "unions_as_p1",
    "unions_as_p2",
    "unions_as_p1__partner1",
    "unions_as_p1__partner2",
    "unions_as_p2__partner1",
    "unions_as_p2__partner2",
    "unions_as_p1__children",
    "unions_as_p2__children",
    "child_of_family",
    "child_of_family__partner1",
    "child_of_family__partner2",
  ).filter(id__in=included_ids)

  return [_format_person_data(person, included_ids) for person in people]


# --------------------------------------------------------------------------------------
# list querysets
# --------------------------------------------------------------------------------------


def get_families_queryset(query):
  """Filtered + ordered family queryset for the family list."""
  families = Family.objects.select_related("partner1", "partner2")
  if query:
    families = families.filter(
      Q(partner1__first_name__icontains=query)
      | Q(partner2__first_name__icontains=query)
      | Q(partner1__last_name__icontains=query)
      | Q(partner2__last_name__icontains=query)
    )
  return families.order_by("id")


# Allowlist of sortable columns: maps the GET `sort` value to the model fields
# used for ordering. Also guards against arbitrary order_by injection.
PERSON_SORT_FIELDS = {
  "name": ["last_name", "first_name"],
  "birth_date": ["birth_date"],
  "birth_place": ["birth_place"],
}


def get_people_queryset(query, sort="name", direction="asc"):
  """Filtered + ordered person queryset for the person list.

  ``sort``/``direction`` mirror the request.GET values; unknown sort keys fall
  back to "name" via the PERSON_SORT_FIELDS allowlist.
  """
  people = (
    Person.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query)) if query else Person.objects.all()
  )

  if sort not in PERSON_SORT_FIELDS:
    sort = "name"
  order_fields = PERSON_SORT_FIELDS[sort]
  prefix = "-" if direction == "desc" else ""
  return people.order_by(*(prefix + field for field in order_fields))


# --------------------------------------------------------------------------------------
# gedcom import
# --------------------------------------------------------------------------------------


def do_import_gedcom(gedcom_file):
  """Import a GEDCOM upload, returning ``(success, message)``.

  ``gedcom_file`` is the uploaded file (``request.FILES["gedcom_file"]``); it is
  written to a temp path, parsed, then removed. Clears genealogy caches on
  success. Messaging + redirect are left to the caller (view).
  """
  path = default_storage.save("tmp/" + gedcom_file.name, ContentFile(gedcom_file.read()))
  try:
    parser = GedcomParser(path)
    # Parse + DB writes as one transaction: a failure mid-import rolls back the partially
    # imported persons/families instead of leaving a broken genealogy.
    with transaction.atomic():
      parser.parse()
    clear_genealogy_caches()
    return (True, _("GEDCOM imported successfully."))
  except Exception as e:
    return (False, _("Error importing GEDCOM: %(error)s") % {"error": str(e)})
  finally:
    default_storage.delete(path)
