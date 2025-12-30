from django.test import TestCase
from django.utils.translation import gettext as _
from django.urls import reverse
from datetime import date
from django.utils import formats
from .models import Person, Family
from .forms import PersonForm, FamilyForm
from members.tests.tests_member_base import MemberTestCase


class PersonModelTest(TestCase):
  def setUp(self):
    super().setUp()
    self.person = Person.objects.create(first_name="John", last_name="Doe", sex="M", birth_date=date(1990, 1, 1))

  def test_person_creation(self):
    self.assertTrue(isinstance(self.person, Person))
    self.assertEqual(self.person.__str__(), "John Doe")

  def test_person_age(self):
    # Age calculation depends on today's date
    today = date.today()
    expected_age = today.year - 1990 - ((today.month, today.day) < (1, 1))
    self.assertEqual(self.person.age, expected_age)

  def test_person_death_age(self):
    self.person.death_date = date(2020, 1, 1)
    self.person.save()
    # Age at death: 2020 - 1990 = 30 (died on birthday)
    self.assertEqual(self.person.age, 30)


class FamilyModelTest(TestCase):
  def setUp(self):
    super().setUp()
    self.p1 = Person.objects.create(first_name="P1", last_name="Test", sex="M")
    self.p2 = Person.objects.create(first_name="P2", last_name="Test", sex="F")
    self.family = Family.objects.create(
      partner1=self.p1,
      partner2=self.p2,
      union_type="MARR",
      union_date=date(2010, 6, 15),
    )

  def test_family_creation(self):
    self.assertTrue(isinstance(self.family, Family))
    self.assertEqual(self.family.__str__(), "P1 Test & P2 Test")

  def test_partners_relationship(self):
    partners_p1 = self.p1.get_partners()
    self.assertIn(self.p2, partners_p1)

    partners_p2 = self.p2.get_partners()
    self.assertIn(self.p1, partners_p2)

  def test_children_relationship(self):
    child = Person.objects.create(first_name="Child", last_name="Test", sex="M", child_of_family=self.family)
    self.assertIn(child, self.family.children.all())


class GenealogyViewsTest(MemberTestCase):
  def setUp(self):
    super().setUp()
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

  def test_dashboard_view(self):
    response = self.client.get(reverse("genealogy:dashboard"), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/dashboard.html")
    self.assertContains(
      response,
      f"""<div class='box'>
            <div class='heading'>{_("Total People")}</div>
            <div class='title'>{Person.objects.count()}</div>
        </div>""",
      html=True,
    )
    self.assertContains(
      response,
      f"""<div class='box'>
            <div class='heading'>{_("Total Families")}</div>
            <div class='title'>{Family.objects.count()}</div>
        </div>""",
      html=True,
    )

  def test_person_list_view(self):
    response = self.client.get(reverse("genealogy:person_list"), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "Test, View_P1")
    self.assertContains(response, formats.date_format(self.p1.birth_date, "DATE_FORMAT"))
    self.assertContains(response, "Test, View_P2")
    self.assertContains(response, formats.date_format(self.p2.birth_date, "DATE_FORMAT"))
    self.assertContains(response, "Test, View_P3")
    self.assertContains(response, formats.date_format(self.p3.birth_date, "DATE_FORMAT"))

  def test_person_detail_view(self):
    response = self.client.get(reverse("genealogy:person_detail", args=[self.p1.id]), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "View_P1 Test")
    self.assertContains(response, formats.date_format(self.p1.birth_date, "DATE_FORMAT"))
    self.assertContains(response, formats.date_format(self.p1.death_date, "DATE_FORMAT"))

  def test_family_chart_view(self):
    response = self.client.get(reverse("genealogy:family_chart"), follow=True)
    self.assertEqual(response.status_code, 200)

  def test_family_chart_data_api(self):
    response = self.client.get(
      reverse("genealogy:family_chart_data"),
      follow=True,
      headers={"HTTP_ACCEPT": "application/json"},
    )
    self.assertEqual(response.status_code, 200)
    data = response.json()
    # print(data)
    persons = [self.p1, self.p2, self.p3]
    for i in range(3):
      self.assertEqual(data[i]["id"], str(persons[i].id))
      self.assertEqual(data[i]["data"]["first name"], persons[i].first_name)
      self.assertEqual(data[i]["data"]["last name"], persons[i].last_name)
      self.assertEqual(data[i]["data"]["gender"], persons[i].sex)
      if persons[i].birth_date:
        self.assertEqual(data[i]["data"]["birthday"], formats.date_format(persons[i].birth_date, "SHORT_DATE_FORMAT"))
      if persons[i].death_date:
        self.assertEqual(data[i]["data"]["deathday"], formats.date_format(persons[i].death_date, "SHORT_DATE_FORMAT"))
      spouses = persons[i].get_partners()
      if spouses:
        self.assertSetEqual(set([str(spouse.id) for spouse in spouses]), set(data[i]["rels"]["spouses"]))
      children = [
        p.id
        for p in persons
        if p.id != persons[i].id
        and p.child_of_family
        and (p.child_of_family.partner1 == persons[i].id or p.child_of_family.partner2 == persons[i].id)
      ]
      if children:
        self.assertSetEqual(set(children), set(data[i]["rels"]["children"]))


class GenealogyFormsTest(TestCase):
  def test_person_form_valid(self):
    form = PersonForm(
      data={
        "first_name": "Form",
        "last_name": "Test",
        "sex": "M",
        "birth_date": "2000-01-01",
      }
    )
    self.assertTrue(form.is_valid(), form.errors)

  def test_family_form_valid(self):
    p1 = Person.objects.create(first_name="F1", last_name="T", sex="M")
    p2 = Person.objects.create(first_name="F2", last_name="T", sex="F")
    form = FamilyForm(
      data={
        "partner1": p1.id,
        "partner2": p2.id,
        "union_type": "MARR",
        "union_date": "2010-01-01",
      }
    )
    self.assertTrue(form.is_valid(), form.errors)
