import os
import tempfile
import uuid
from datetime import date
from django.test import TestCase
from django.core.cache import cache
from ..models import Person, Family
from ..utils import GedcomParser, GedcomExporter, register_genealogy_cache, clear_genealogy_caches


class GedcomParserTests(TestCase):
  def setUp(self):
    self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ged", mode="w", encoding="utf-8")
    self.gedcom_content = """0 HEAD
1 GEDC
2 VERS 5.5.1
1 CHAR UTF-8
0 @I1@ INDI
1 NAME John /Doe/
2 GIVN John
2 SURN Doe
1 SEX M
1 BIRT
2 DATE 01 JAN 1990
2 PLAC New York
1 _UID 550E8400E29B41D4A716446655440000
0 @I2@ INDI
1 NAME Jane /Smith/
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
0 @I3@ INDI
1 NAME Baby /Doe/
1 SEX M
0 TRLR
"""
    self.temp_file.write(self.gedcom_content)
    self.temp_file.close()

  def tearDown(self):
    if os.path.exists(self.temp_file.name):
      os.remove(self.temp_file.name)

  def test_parse_date(self):
    parser = GedcomParser(self.temp_file.name)
    self.assertEqual(parser._parse_date("1990-01-01"), date(1990, 1, 1))
    self.assertEqual(parser._parse_date("01 JAN 1990"), date(1990, 1, 1))
    self.assertEqual(parser._parse_date("1990"), date(1990, 1, 1))
    self.assertIsNone(parser._parse_date(""))
    self.assertIsNone(parser._parse_date("INVALID"))

  def test_create_person(self):
    parser = GedcomParser(self.temp_file.name)

    class MockElement:
      def get_name(self):
        return ("John", "Doe")

      def get_pointer(self):
        return "@I1@"

      def get_gender(self):
        return "M"

      # Birth data returns (date, place)
      # If place is None, utils.py _create_person will set birth_place=None
      # which fails because the model field is blank=True but not null=True
      def get_birth_data(self):
        return ("01 JAN 1990", "New York")

      def get_death_data(self):
        return (None, "")  # Return empty string instead of None

      def get_child_elements(self):
        class MockChild:
          def get_tag(self):
            return "_UID"

          def get_value(self):
            return "550e8400-e29b-41d4-a716-446655440000"

        return [MockChild()]

    person = parser._create_person(MockElement())
    self.assertEqual(person.first_name, "John")
    self.assertEqual(person.last_name, "Doe")
    self.assertEqual(person.sex, "M")
    self.assertEqual(person.birth_date, date(1990, 1, 1))
    self.assertEqual(person.uid, uuid.UUID("550e8400-e29b-41d4-a716-446655440000"))

  def test_full_parse(self):
    parser = GedcomParser(self.temp_file.name)
    parser.parse()

    self.assertEqual(Person.objects.count(), 3)
    john = Person.objects.get(first_name="John")
    jane = Person.objects.get(first_name="Jane")
    baby = Person.objects.get(first_name="Baby")

    self.assertEqual(john.sex, "M")
    self.assertEqual(jane.sex, "F")
    self.assertEqual(Family.objects.count(), 1)

    family = Family.objects.first()
    self.assertEqual(family.partner1, john)
    self.assertEqual(family.partner2, jane)
    self.assertEqual(baby.child_of_family, family)


class GedcomExporterTests(TestCase):
  def setUp(self):
    self.p1 = Person.objects.create(
      first_name="John",
      last_name="Doe",
      sex="M",
      birth_date=date(1990, 1, 1),
      uid=uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
    )
    self.p2 = Person.objects.create(first_name="Jane", last_name="Smith", sex="F")
    self.family = Family.objects.create(partner1=self.p1, partner2=self.p2)
    self.child = Person.objects.create(first_name="Baby", last_name="Doe", sex="M", child_of_family=self.family)

  def test_export_individual(self):
    exporter = GedcomExporter()
    lines = exporter._export_individual(self.p1)
    content = "\n".join(lines)
    self.assertIn(f"0 @I{self.p1.id}@ INDI", content)
    self.assertIn("1 NAME John /Doe/", content)
    self.assertIn("1 SEX M", content)
    self.assertIn("1 _UID 550E8400E29B41D4A716446655440000", content)

  def test_export_family(self):
    exporter = GedcomExporter()
    lines = exporter._export_family(self.family)
    content = "\n".join(lines)
    self.assertIn(f"0 @F{self.family.id}@ FAM", content)
    self.assertIn(f"1 HUSB @I{self.p1.id}@", content)
    self.assertIn(f"1 WIFE @I{self.p2.id}@", content)
    self.assertIn(f"1 CHIL @I{self.child.id}@", content)

  def test_full_export(self):
    exporter = GedcomExporter()
    gedcom_text = exporter.export()
    self.assertIn("0 HEAD", gedcom_text)
    self.assertIn(f"0 @I{self.p1.id}@ INDI", gedcom_text)
    self.assertIn(f"0 @F{self.family.id}@ FAM", gedcom_text)
    self.assertIn("0 TRLR", gedcom_text)


class GenealogyCacheTests(TestCase):
  def test_cache_registration_and_clearing(self):
    cache_name = "test_genealogy_cache"
    register_genealogy_cache(cache_name)

    cache.set(cache_name, "some_data")
    self.assertEqual(cache.get(cache_name), "some_data")

    clear_genealogy_caches()
    self.assertIsNone(cache.get(cache_name))
