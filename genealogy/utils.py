import logging
from datetime import datetime
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from django.db.models import Q
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
        birth_place = birth_data[1]

        death_date = self._parse_date(death_data[0]) if death_data[0] else None
        death_place = death_data[1]

        # Map sex to model choices
        sex_map = {"M": "M", "F": "F"}
        model_sex = sex_map.get(sex, "O")

        person, created = Person.objects.update_or_create(
            gedcom_id=gedcom_id,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "sex": model_sex,
                "birth_date": birth_date,
                "birth_place": birth_place,
                "death_date": death_date,
                "death_place": death_place,
            },
        )
        self.person_map[gedcom_id] = person
        return person

    def _create_family(self, element):
        # In python-gedcom, getting family members might need direct traversal
        # This depends on the library version, assuming standard methods or manual traversal

        # Note: python-gedcom 1.0.0 might not have helper methods for everything
        # We might need to look at sub-elements

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

        partner1 = self.person_map.get(husband_id)
        partner2 = self.person_map.get(wife_id)

        if partner1 or partner2:
            # Try to find existing family with these partners to avoid duplicates
            family = None
            if partner1 and partner2:
                family = Family.objects.filter(
                    partner1=partner1, partner2=partner2
                ).first()
            elif partner1:
                family = Family.objects.filter(
                    partner1=partner1, partner2__isnull=True
                ).first()
            elif partner2:
                family = Family.objects.filter(
                    partner1__isnull=True, partner2=partner2
                ).first()

            if not family:
                family = Family.objects.create(
                    partner1=partner1,
                    partner2=partner2,
                    union_type="MARR",
                )

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
    def export(self):
        lines = [
            "0 HEAD",
            "1 SOUR CousinsMatter",
            "1 GEDC",
            "2 VERS 5.5.1",
            "2 FORM LINEAGE-LINKED",
            "1 CHAR UTF-8",
        ]

        # Individuals
        for person in Person.objects.all():
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

        # Families
        for family in Family.objects.all():
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

        lines.append("0 TRLR")
        return "\n".join(lines)
