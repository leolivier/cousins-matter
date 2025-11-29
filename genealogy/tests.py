from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from .models import Person, Family
from .forms import PersonForm, FamilyForm


class PersonModelTest(TestCase):
    def setUp(self):
        self.person = Person.objects.create(
            first_name="John", last_name="Doe", sex="M", birth_date=date(1990, 1, 1)
        )

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
        child = Person.objects.create(
            first_name="Child", last_name="Test", sex="M", child_of_family=self.family
        )
        self.assertIn(child, self.family.children.all())


class GenealogyViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.person = Person.objects.create(
            first_name="View", last_name="Test", sex="F"
        )
        self.family = Family.objects.create(partner1=self.person, union_type="MARR")

    def test_dashboard_view(self):
        response = self.client.get(reverse("genealogy:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "genealogy/dashboard.html")

    def test_person_list_view(self):
        response = self.client.get(reverse("genealogy:person_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test, View")

    def test_person_detail_view(self):
        response = self.client.get(
            reverse("genealogy:person_detail", args=[self.person.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Test")

    def test_family_tree_view(self):
        response = self.client.get(reverse("genealogy:family_tree"))
        self.assertEqual(response.status_code, 200)

    def test_tree_data_api(self):
        response = self.client.get(reverse("genealogy:tree_data"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("nodes", data)
        self.assertIn("links", data)


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
        self.assertTrue(form.is_valid())

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
        self.assertTrue(form.is_valid())
