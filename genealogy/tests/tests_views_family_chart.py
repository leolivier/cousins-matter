from datetime import date
from django.urls import reverse
from django.utils import formats
from django.core.cache import cache
from ..models import Person, Family
from members.tests.tests_member_base import MemberTestCase
from ..views.views_family_chart import CACHE_KEY_FAMILY_CHART_DATA


class FamilyChartViewsTest(MemberTestCase):
  def setUp(self):
    super().setUp()
    cache.clear()
    self.p1 = Person.objects.create(
      first_name="View_P1",
      last_name="Test",
      sex="F",
      birth_date=date(1990, 1, 1),
      death_date=date(2025, 1, 1),
    )
    self.p2 = Person.objects.create(
      first_name="View_P2",
      last_name="Test",
      sex="M",
      birth_date=date(1990, 1, 1),
      death_date=date(2025, 1, 1),
    )
    self.family = Family.objects.create(partner1=self.p1, partner2=self.p2, union_type="MARR")
    self.p3 = Person.objects.create(
      first_name="View_P3",
      last_name="Test",
      sex="M",
      birth_date=date(2020, 1, 1),
      child_of_family=self.family,
    )

  def test_family_chart_view(self):
    # Test without main_person_id
    response = self.client.get(reverse("genealogy:family_chart"), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/family_chart.html")
    self.assertIsNone(response.context["main_person_id"])

    # Test with main_person_id
    response = self.client.get(reverse("genealogy:person_chart", args=[self.p1.id]), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.context["main_person_id"], self.p1.id)

  def test_family_chart_data_api(self):
    response = self.client.get(
      reverse("genealogy:family_chart_data"),
      follow=True,
      headers={"HTTP_ACCEPT": "application/json"},
    )
    self.assertEqual(response.status_code, 200)
    data = response.json()

    persons = [self.p1, self.p2, self.p3]
    person_ids = [str(p.id) for p in persons]

    # Verify all persons are in data
    returned_ids = [item["id"] for item in data]
    for p_id in person_ids:
      self.assertIn(p_id, returned_ids)

    # Check P1 data specifically
    p1_data = next(item for item in data if item["id"] == str(self.p1.id))
    self.assertEqual(p1_data["data"]["first name"], "View_P1")
    self.assertEqual(p1_data["data"]["gender"], "F")
    self.assertEqual(p1_data["data"]["birthday"], formats.date_format(self.p1.birth_date, "SHORT_DATE_FORMAT"))
    self.assertEqual(p1_data["data"]["deathday"], formats.date_format(self.p1.death_date, "SHORT_DATE_FORMAT"))

    # Check relationships for P1
    self.assertIn(str(self.p2.id), p1_data["rels"]["spouses"])
    self.assertIn(str(self.p3.id), p1_data["rels"]["children"])

  def test_family_chart_data_caching(self):
    # Initial request to populate cache
    response = self.client.get(reverse("genealogy:family_chart_data"))
    self.assertEqual(response.status_code, 200)

    # Verify cache is populated
    cached_data = cache.get(CACHE_KEY_FAMILY_CHART_DATA)
    self.assertIsNotNone(cached_data)
    self.assertEqual(len(cached_data), Person.objects.count())

    # Modify a person in DB
    self.p1.first_name = "Updated_Name"
    self.p1.save()

    # Request again - should return cached data (old name)
    response = self.client.get(reverse("genealogy:family_chart_data"))
    data = response.json()
    p1_data = next(item for item in data if item["id"] == str(self.p1.id))
    self.assertEqual(p1_data["data"]["first name"], "View_P1")

    # Clear cache and request - should return updated data
    cache.clear()
    response = self.client.get(reverse("genealogy:family_chart_data"))
    data = response.json()
    p1_data = next(item for item in data if item["id"] == str(self.p1.id))
    self.assertEqual(p1_data["data"]["first name"], "Updated_Name")

  def test_family_chart_data_empty_db(self):
    Person.objects.all().delete()
    cache.clear()
    response = self.client.get(reverse("genealogy:family_chart_data"))
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json(), [])

  def test_family_chart_data_complex_relationships(self):
    # Create a second family for P1
    p4 = Person.objects.create(first_name="View_P4", last_name="Other", sex="M")
    family2 = Family.objects.create(partner1=p4, partner2=self.p1, union_type="MARR")
    p5 = Person.objects.create(first_name="View_P5", last_name="Other", sex="F", child_of_family=family2)

    cache.clear()
    response = self.client.get(reverse("genealogy:family_chart_data"))
    data = response.json()

    p1_data = next(item for item in data if item["id"] == str(self.p1.id))

    # Should have two spouses
    self.assertEqual(len(p1_data["rels"]["spouses"]), 2)
    self.assertIn(str(self.p2.id), p1_data["rels"]["spouses"])
    self.assertIn(str(p4.id), p1_data["rels"]["spouses"])

    # Should have two children
    self.assertEqual(len(p1_data["rels"]["children"]), 2)
    self.assertIn(str(self.p3.id), p1_data["rels"]["children"])
    self.assertIn(str(p5.id), p1_data["rels"]["children"])

  def test_family_chart_data_gender_mapping(self):
    p_other = Person.objects.create(first_name="Other", last_name="Person", sex="O")
    p_none = Person.objects.create(first_name="None", last_name="Person", sex="")

    cache.clear()
    response = self.client.get(reverse("genealogy:family_chart_data"))
    data = response.json()

    p_other_data = next(item for item in data if item["id"] == str(p_other.id))
    self.assertEqual(p_other_data["data"]["gender"], "O")

    p_none_data = next(item for item in data if item["id"] == str(p_none.id))
    self.assertEqual(p_none_data["data"]["gender"], "O")  # Default in view is 'O' for non-M/F
