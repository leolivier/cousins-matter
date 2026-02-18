from datetime import date
from unittest.mock import patch
from django.urls import reverse
from django.contrib.messages import get_messages
from ..models import Person
from members.tests.tests_member_base import MemberTestCase


class PersonViewsTest(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.person = Person.objects.create(
      first_name="Alice",
      last_name="Smith",
      sex="F",
      birth_date=date(1990, 1, 1),
    )

  # ── person_list ───────────────────────────────────────────────

  def test_person_list_get(self):
    response = self.client.get(reverse("genealogy:person_list"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/person_list.html")

  def test_person_list_search(self):
    response = self.client.get(reverse("genealogy:person_list"), {"q": "Alice"})
    self.assertEqual(response.status_code, 200)
    people = list(response.context["page"].object_list)
    self.assertIn(self.person, people)

  def test_person_list_search_by_last_name(self):
    response = self.client.get(reverse("genealogy:person_list"), {"q": "Smith"})
    self.assertEqual(response.status_code, 200)
    people = list(response.context["page"].object_list)
    self.assertIn(self.person, people)

  def test_person_list_search_no_match(self):
    response = self.client.get(reverse("genealogy:person_list"), {"q": "ZZZNotExist"})
    self.assertEqual(response.status_code, 200)
    people = list(response.context["page"].object_list)
    self.assertEqual(len(people), 0)

  def test_person_list_pagination(self):
    response = self.client.get(reverse("genealogy:person_list_page", args=[1]))
    self.assertEqual(response.status_code, 200)

  def test_person_list_htmx_uses_fragment_template(self):
    response = self.client.get(
      reverse("genealogy:person_list"),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "person_list_table")

  def test_person_list_page_out_of_bounds_redirects(self):
    response = self.client.get(reverse("genealogy:person_list_page", args=[9999]))
    self.assertEqual(response.status_code, 302)

  # ── person_detail ─────────────────────────────────────────────

  def test_person_detail(self):
    response = self.client.get(reverse("genealogy:person_detail", args=[self.person.pk]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/person_detail.html")
    self.assertEqual(response.context["person"], self.person)

  def test_person_detail_404(self):
    response = self.client.get(reverse("genealogy:person_detail", args=[99999]))
    self.assertEqual(response.status_code, 404)

  # ── person_create ─────────────────────────────────────────────

  def test_person_create_get(self):
    response = self.client.get(reverse("genealogy:person_create"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/person_form.html")
    self.assertIn("form", response.context)

  @patch("genealogy.views.views_person.clear_genealogy_caches")
  def test_person_create_post_valid(self, mock_clear):
    data = {
      "first_name": "Bob",
      "last_name": "Jones",
      "sex": "M",
      "birth_date": "",
      "birth_place": "",
      "death_date": "",
      "death_place": "",
      "notes": "",
    }
    response = self.client.post(reverse("genealogy:person_create"), data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTrue(Person.objects.filter(first_name="Bob", last_name="Jones").exists())
    msgs = [str(m) for m in get_messages(response.wsgi_request)]
    self.assertTrue(len(msgs) > 0)
    mock_clear.assert_called_once()

  def test_person_create_post_invalid(self):
    data = {"first_name": "", "last_name": ""}  # required fields missing
    response = self.client.post(reverse("genealogy:person_create"), data)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/person_form.html")
    self.assertTrue(response.context["form"].errors)

  # ── person_update ─────────────────────────────────────────────

  def test_person_update_get(self):
    response = self.client.get(reverse("genealogy:person_update", args=[self.person.pk]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/person_form.html")
    form = response.context["form"]
    self.assertEqual(form.instance, self.person)

  @patch("genealogy.views.views_person.clear_genealogy_caches")
  def test_person_update_post_valid(self, mock_clear):
    data = {
      "first_name": "Alice",
      "last_name": "Johnson",
      "sex": "F",
      "birth_date": "1990-01-01",
      "birth_place": "Paris",
      "death_date": "",
      "death_place": "",
      "notes": "Updated",
    }
    response = self.client.post(reverse("genealogy:person_update", args=[self.person.pk]), data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.person.refresh_from_db()
    self.assertEqual(self.person.last_name, "Johnson")
    self.assertEqual(self.person.birth_place, "Paris")
    msgs = [str(m) for m in get_messages(response.wsgi_request)]
    self.assertTrue(len(msgs) > 0)
    mock_clear.assert_called_once()

  def test_person_update_post_invalid(self):
    data = {
      "first_name": "",
      "last_name": "",
      "sex": "F",
    }
    response = self.client.post(reverse("genealogy:person_update", args=[self.person.pk]), data)
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.context["form"].errors)

  def test_person_update_404(self):
    response = self.client.get(reverse("genealogy:person_update", args=[99999]))
    self.assertEqual(response.status_code, 404)

  # ── person_delete ─────────────────────────────────────────────

  def test_person_delete_get(self):
    response = self.client.get(reverse("genealogy:person_delete", args=[self.person.pk]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/person_confirm_delete.html")
    self.assertEqual(response.context["person"], self.person)

  @patch("genealogy.views.views_person.clear_genealogy_caches")
  def test_person_delete_post(self, mock_clear):
    pk = self.person.pk
    response = self.client.post(reverse("genealogy:person_delete", args=[pk]), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertFalse(Person.objects.filter(pk=pk).exists())
    msgs = [str(m) for m in get_messages(response.wsgi_request)]
    self.assertTrue(len(msgs) > 0)
    mock_clear.assert_called_once()

  def test_person_delete_404(self):
    response = self.client.get(reverse("genealogy:person_delete", args=[99999]))
    self.assertEqual(response.status_code, 404)
