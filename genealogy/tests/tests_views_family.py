from datetime import date
from unittest.mock import patch
from django.urls import reverse
from django.contrib.messages import get_messages
from ..models import Person, Family
from members.tests.tests_member_base import MemberTestCase


class FamilyViewsTest(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.p1 = Person.objects.create(
      first_name="Alice",
      last_name="Smith",
      sex="F",
      birth_date=date(1990, 1, 1),
    )
    self.p2 = Person.objects.create(
      first_name="Bob",
      last_name="Jones",
      sex="M",
      birth_date=date(1988, 5, 15),
    )
    self.family = Family.objects.create(
      partner1=self.p1,
      partner2=self.p2,
      union_type="MARR",
    )

  # ── family_list ───────────────────────────────────────────────

  def test_family_list_get(self):
    response = self.client.get(reverse("genealogy:family_list"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/family_list.html")
    self.assertContains(response, str(self.family.partner1))
    self.assertContains(response, str(self.family.partner2))

  def test_family_list_search_by_partner1_first_name(self):
    response = self.client.get(reverse("genealogy:family_list"), {"q": "Alice"})
    self.assertEqual(response.status_code, 200)
    families = list(response.context["page"].object_list)
    self.assertIn(self.family, families)

  def test_family_list_search_by_partner2_last_name(self):
    response = self.client.get(reverse("genealogy:family_list"), {"q": "Jones"})
    self.assertEqual(response.status_code, 200)
    families = list(response.context["page"].object_list)
    self.assertIn(self.family, families)

  def test_family_list_search_no_match(self):
    response = self.client.get(reverse("genealogy:family_list"), {"q": "ZZZNotExist"})
    self.assertEqual(response.status_code, 200)
    families = list(response.context["page"].object_list)
    self.assertEqual(len(families), 0)

  def test_family_list_pagination(self):
    response = self.client.get(reverse("genealogy:family_list_page", args=[1]))
    self.assertEqual(response.status_code, 200)

  def test_family_list_htmx_uses_fragment_template(self):
    response = self.client.get(
      reverse("genealogy:family_list"),
      HTTP_HX_REQUEST="true",
    )
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "family_list_table")

  def test_family_list_page_out_of_bounds_redirects(self):
    response = self.client.get(reverse("genealogy:family_list_page", args=[9999]))
    self.assertEqual(response.status_code, 302)

  # ── family_create ─────────────────────────────────────────────

  def test_family_create_get(self):
    response = self.client.get(reverse("genealogy:family_create"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/family_form.html")
    self.assertIn("form", response.context)

  @patch("genealogy.views.views_family.clear_genealogy_caches")
  def test_family_create_post_valid(self, mock_clear):
    p3 = Person.objects.create(first_name="Carol", last_name="Doe", sex="F")
    p4 = Person.objects.create(first_name="Dan", last_name="Doe", sex="M")
    data = {
      "partner1": p3.pk,
      "partner2": p4.pk,
      "union_type": "CIVI",
      "union_date": "",
      "union_place": "",
      "separation_date": "",
    }
    response = self.client.post(reverse("genealogy:family_create"), data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTrue(Family.objects.filter(partner1=p3, partner2=p4).exists())
    msgs = [str(m) for m in get_messages(response.wsgi_request)]
    self.assertTrue(len(msgs) > 0)
    mock_clear.assert_called_once()

  def test_family_create_post_invalid(self):
    data = {"union_type": "INVALID"}
    response = self.client.post(reverse("genealogy:family_create"), data)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/family_form.html")
    self.assertTrue(response.context["form"].errors)

  # ── family_update ─────────────────────────────────────────────

  def test_family_update_get(self):
    response = self.client.get(reverse("genealogy:family_update", args=[self.family.pk]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/family_form.html")
    form = response.context["form"]
    self.assertEqual(form.instance, self.family)

  @patch("genealogy.views.views_family.clear_genealogy_caches")
  def test_family_update_post_valid(self, mock_clear):
    data = {
      "partner1": self.p1.pk,
      "partner2": self.p2.pk,
      "union_type": "COHA",
      "union_date": "",
      "union_place": "Paris",
      "separation_date": "",
    }
    response = self.client.post(reverse("genealogy:family_update", args=[self.family.pk]), data, follow=True)
    self.assertEqual(response.status_code, 200)
    self.family.refresh_from_db()
    self.assertEqual(self.family.union_type, "COHA")
    self.assertEqual(self.family.union_place, "Paris")
    msgs = [str(m) for m in get_messages(response.wsgi_request)]
    self.assertTrue(len(msgs) > 0)
    mock_clear.assert_called_once()

  def test_family_update_post_invalid(self):
    data = {
      "partner1": self.p1.pk,
      "partner2": self.p2.pk,
      "union_type": "INVALID",
      "union_date": "",
      "union_place": "",
      "separation_date": "",
    }
    response = self.client.post(reverse("genealogy:family_update", args=[self.family.pk]), data)
    self.assertEqual(response.status_code, 200)
    self.assertTrue(response.context["form"].errors)

  def test_family_update_404(self):
    response = self.client.get(reverse("genealogy:family_update", args=[99999]))
    self.assertEqual(response.status_code, 404)

  # ── family_delete ─────────────────────────────────────────────

  def test_family_delete_get(self):
    response = self.client.get(reverse("genealogy:family_delete", args=[self.family.pk]))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/family_confirm_delete.html")
    self.assertEqual(response.context["family"], self.family)

  @patch("genealogy.views.views_family.clear_genealogy_caches")
  def test_family_delete_post(self, mock_clear):
    pk = self.family.pk
    response = self.client.post(reverse("genealogy:family_delete", args=[pk]), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertFalse(Family.objects.filter(pk=pk).exists())
    msgs = [str(m) for m in get_messages(response.wsgi_request)]
    self.assertTrue(len(msgs) > 0)
    mock_clear.assert_called_once()

  def test_family_delete_404(self):
    response = self.client.get(reverse("genealogy:family_delete", args=[99999]))
    self.assertEqual(response.status_code, 404)
