from django.urls import reverse
from django.utils.translation import gettext as _
from unittest.mock import patch
from datetime import date
from .models import Person, Family
from members.tests.tests_member_base import MemberTestCase


class DashboardStatsViewsTest(MemberTestCase):
  def setUp(self):
    super().setUp()
    # Create some data for testing
    self.p1 = Person.objects.create(first_name="Alice", last_name="Smith", sex="F", birth_date=date(1980, 5, 12))
    self.p2 = Person.objects.create(first_name="Bob", last_name="Jones", sex="M", birth_date=date(1975, 8, 20))
    self.p3 = Person.objects.create(first_name="Charlie", last_name="Smith", sex="M", birth_date=date(1985, 3, 15))
    self.family = Family.objects.create(partner1=self.p1, partner2=self.p2)

  def test_dashboard_view(self):
    response = self.client.get(reverse("genealogy:dashboard"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/dashboard.html")
    self.assertEqual(response.context["total_people"], 3)
    self.assertEqual(response.context["total_families"], 1)

  def test_statistics_view_gender_distribution(self):
    response = self.client.get(reverse("genealogy:statistics"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "genealogy/statistics.html")

    gender_data = response.context["gender_data"]
    # Expecting counts for M and F
    # [{'sex': 'F', 'count': 1}, {'sex': 'M', 'count': 2}] (order might vary)
    m_count = next(item["count"] for item in gender_data if item["sex"] == "M")
    f_count = next(item["count"] for item in gender_data if item["sex"] == "F")
    self.assertEqual(m_count, 2)
    self.assertEqual(f_count, 1)

  def test_statistics_view_top_names(self):
    response = self.client.get(reverse("genealogy:statistics"))
    self.assertEqual(response.status_code, 200)

    top_last_names = response.context["top_last_names"]
    # Smith (2), Jones (1)
    self.assertEqual(top_last_names[0]["last_name"], "Smith")
    self.assertEqual(top_last_names[0]["count"], 2)
    self.assertEqual(top_last_names[1]["last_name"], "Jones")
    self.assertEqual(top_last_names[1]["count"], 1)

  def test_statistics_view_decades(self):
    response = self.client.get(reverse("genealogy:statistics"))
    self.assertEqual(response.status_code, 200)

    decades = response.context["decades"]
    births_per_decade = response.context["births_per_decade"]

    # 1975 -> 1970 decade (1)
    # 1980 -> 1980 decade (1)
    # 1985 -> 1980 decade (1)
    # So 1970: 1, 1980: 2
    self.assertIn(1970, decades)
    self.assertIn(1980, decades)

    idx_1970 = decades.index(1970)
    idx_1980 = decades.index(1980)

    self.assertEqual(births_per_decade[idx_1970], 1)
    self.assertEqual(births_per_decade[idx_1980], 2)

  @patch("genealogy.views.views_dashboard_stats.clear_genealogy_caches")
  def test_refresh_view(self, mock_clear_caches):
    # We need a referer to redirect back
    referer = "/some-page/"
    response = self.client.get(reverse("genealogy:refresh"), HTTP_REFERER=referer)

    self.assertRedirects(response, referer, fetch_redirect_response=False)
    mock_clear_caches.assert_called_once()

    # Check success message
    from django.contrib.messages import get_messages

    messages = list(get_messages(response.wsgi_request))
    self.assertEqual(len(messages), 1)
    self.assertEqual(str(messages[0]), _("Genealogy data refreshed successfully."))
