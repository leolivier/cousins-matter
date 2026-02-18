import logging
import uuid
from datetime import datetime
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from django.conf import settings
from django.db.models import Q
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from .models import Person, Family

logger = logging.getLogger(__name__)


class GedcomParser:
  def __init__(self, file_path):
    self.file_path = file_path
    self.gedcom = Parser()
    self.gedcom.parse_file(self.file_path)
    self.person_map = {}  # Map GEDCOM ID to Person object

  def parse(self):
    root_child_elements = self.gedcom.get_root_child_elements()

    # First pass: Create all individuals
    for element in root_child_elements:
      if isinstance(element, IndividualElement):
        self._create_person(element)

    # Second pass: Create families and link relationships
    for element in root_child_elements:
      if isinstance(element, FamilyElement):
        self._create_family(element)

  def _create_person(self, element):
    first_name, last_name = element.get_name()
    gedcom_id = element.get_pointer()
    sex = element.get_gender()
    birth_data = element.get_birth_data()
    death_data = element.get_death_data()

    birth_date = self._parse_date(birth_data[0]) if birth_data[0] else None
    birth_place = birth_data[1] or ""

    death_date = self._parse_date(death_data[0]) if death_data[0] else None
    death_place = death_data[1] or ""

    # Extract _UID if present
    uid_hex = None
    for child in element.get_child_elements():
      if child.get_tag() == "_UID":
        uid_hex = child.get_value().strip()
        break

    # Map sex to model choices
    sex_map = {"M": "M", "F": "F"}
    model_sex = sex_map.get(sex, "O")

    person_defaults = {
      "first_name": first_name,
      "last_name": last_name,
      "sex": model_sex,
      "birth_date": birth_date,
      "birth_place": birth_place,
      "death_date": death_date,
      "death_place": death_place,
    }

    if uid_hex:
      try:
        # Some Gedcoms use 32 hex chars, some use UUID string format
        if len(uid_hex) == 32:
          person_defaults["uid"] = uuid.UUID(hex=uid_hex)
        else:
          person_defaults["uid"] = uuid.UUID(uid_hex)
      except ValueError:
        logger.warning(f"Invalid _UID format: {uid_hex} for person {gedcom_id}")

    person, _ = Person.objects.update_or_create(
      gedcom_id=gedcom_id,
      defaults=person_defaults,
    )
    self.person_map[gedcom_id] = person
    return person

  def _extract_family_members(self, element):
    husband_id = None
    wife_id = None
    children_ids = []

    for child in element.get_child_elements():
      tag = child.get_tag()
      if tag == "HUSB":
        husband_id = child.get_value()
      elif tag == "WIFE":
        wife_id = child.get_value()
      elif tag == "CHIL":
        children_ids.append(child.get_value())

    return husband_id, wife_id, children_ids

  def _find_or_create_family(self, partner1, partner2):
    family = None
    if partner1 and partner2:
      family = Family.objects.filter(partner1=partner1, partner2=partner2).first()
    elif partner1:
      family = Family.objects.filter(partner1=partner1, partner2__isnull=True).first()
    elif partner2:
      family = Family.objects.filter(partner1__isnull=True, partner2=partner2).first()

    if not family:
      family = Family.objects.create(
        partner1=partner1,
        partner2=partner2,
        union_type="MARR",
      )
    return family

  def _create_family(self, element):
    husband_id, wife_id, children_ids = self._extract_family_members(element)

    partner1 = self.person_map.get(husband_id)
    partner2 = self.person_map.get(wife_id)

    if partner1 or partner2:
      family = self._find_or_create_family(partner1, partner2)

      # Update/Link children
      for child_id in children_ids:
        child = self.person_map.get(child_id)
        if child:
          child.child_of_family = family
          child.save()

  def _parse_date(self, date_str):
    if not date_str:
      return None
    # Very basic parsing, GEDCOM dates are complex (e.g. "ABT 1990", "JAN 1980")
    # For MVP, try to extract year at least, or full date if simple
    try:
      # Try YYYY-MM-DD
      return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
      pass

    try:
      # Try DD MON YYYY
      return datetime.strptime(date_str, "%d %b %Y").date()
    except ValueError:
      pass

    # Try just year
    import re

    match = re.search(r"\d{4}", date_str)
    if match:
      return datetime(int(match.group(0)), 1, 1).date()

    return None


class GedcomExporter:
  def _get_gedcom_header(self):
    now = datetime.now()
    nindi = Person.objects.count()
    nfam = Family.objects.count()
    return [
      "0 HEAD",
      "1 GEDC",
      "2 VERS 5.5.1",
      "2 FORM LINEAGE-LINKED",
      "1 CHAR UTF-8",
      "1 DEST CousinsMatter",
      "1 SOUR CousinsMatter",
      f"2 VERS {settings.APP_VERSION}",
      "2 NAME CousinsMatter",
      "2 CORP CousinsMatter",
      "1 SUBM @U0@",
      f"1 DATE {now.strftime('%d %b %Y')}",
      f"2 TIME {now.strftime('%H:%M:%S.%f')[:6]}",
      "1 LANG English",
      f"1 FILE {settings.GEDCOM_FILE}",
      "1 COPR © 2025 CousinsMatter",
      f"1 _TITL {settings.SITE_NAME}",
      "1 _STS",
      f"2 INDI {nindi}",
      f"2 FAM {nfam}",
      "2 REPO 0",
      "2 SOUR 1",
      "2 NOTE 0",
      "2 SUBM 1",
      "2 OBJE 0",
      "2 _TASK 0",
      "0 @U0@ SUBM",
      "1 NAME CousinsMatter",
      "1 CHAN",
      "2 DATE 30 DEC 2015",
    ]

  def _export_individual(self, person):
    lines = []
    p_id = person.gedcom_id if person.gedcom_id else f"@I{person.id}@"
    # Ensure proper format if stored id is raw text
    if not p_id.startswith("@"):
      p_id = f"@{p_id}@"

    lines.append(f"0 {p_id} INDI")
    lines.append(f"1 NAME {person.first_name} /{person.last_name}/")
    lines.append(f"2 GIVN {person.first_name}")
    lines.append(f"2 SURN {person.last_name}")

    sex_map = {"M": "M", "F": "F"}
    lines.append(f"1 SEX {sex_map.get(person.sex, 'U')}")
    lines.append(f"1 _UID {person.uid.hex.upper()}")

    if person.birth_date:
      lines.append("1 BIRT")
      lines.append(f"2 DATE {person.birth_date.strftime('%d %b %Y').upper()}")
      if person.birth_place:
        lines.append(f"2 PLAC {person.birth_place}")

    if person.death_date:
      lines.append("1 DEAT")
      lines.append(f"2 DATE {person.death_date.strftime('%d %b %Y').upper()}")
      if person.death_place:
        lines.append(f"2 PLAC {person.death_place}")

    # Families where this person is a partner (FAMS)
    families = Family.objects.filter(Q(partner1=person) | Q(partner2=person))
    for family in families:
      lines.append(f"1 FAMS @F{family.id}@")

    # Family where this person is a child (FAMC)
    if person.child_of_family:
      lines.append(f"1 FAMC @F{person.child_of_family.id}@")
    return lines

  def _export_family(self, family):
    lines = []
    lines.append(f"0 @F{family.id}@ FAM")
    if family.partner1:
      lines.append(f"1 HUSB @I{family.partner1.id}@")
    if family.partner2:
      lines.append(f"1 WIFE @I{family.partner2.id}@")

    for child in family.children.all():
      lines.append(f"1 CHIL @I{child.id}@")

    if family.union_date:
      lines.append("1 MARR")
      lines.append(f"2 DATE {family.union_date.strftime('%d %b %Y').upper()}")
      if family.union_place:
        lines.append(f"2 PLAC {family.union_place}")
    return lines

  def export(self):
    lines = self._get_gedcom_header()

    # Individuals
    for person in Person.objects.all():
      lines.extend(self._export_individual(person))

    # Families
    for family in Family.objects.all():
      lines.extend(self._export_family(family))

    lines.append("0 TRLR")
    return "\n".join(lines)


genealogy_caches: set[str] = set()


def register_genealogy_cache(cache_name: str):
  global genealogy_caches
  genealogy_caches.add(cache_name)


def clear_genealogy_caches():
  for cache_name in genealogy_caches:
    # Try direct delete
    cache.delete(cache_name)
    # Try template fragment delete
    fragment_key = make_template_fragment_key(cache_name)
    cache.delete(fragment_key)
    logger.info(f"Cleared cache: {cache_name}")
