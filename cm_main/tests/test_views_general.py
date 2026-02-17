from django.test import TestCase
from django.urls import reverse
from django.db.utils import DatabaseError
from unittest.mock import patch
import redis
from cm_main.forms import PasswordResetForm


class GeneralViewsTestCase(TestCase):
  def test_home_view(self):
    """Test that HomeView returns 200 and uses the correct template."""
    response = self.client.get(reverse("cm_main:Home"))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "cm_main/base.html")

  def test_password_reset_view(self):
    """Test that PasswordResetView uses the custom form."""
    response = self.client.get(reverse("reset_password"))
    self.assertEqual(response.status_code, 200)
    self.assertIsInstance(response.context["form"], PasswordResetForm)
    self.assertTemplateUsed(response, "members/login/password_reset.html")


class HealthCheckTestCase(TestCase):
  def test_health_ok(self):
    """Test health view returns 200 status when everything is OK."""
    with patch("cm_main.views.views_general.redis_client") as mock_redis:
      mock_redis.ping.return_value = True
      response = self.client.get(reverse("health"))
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.json(), {"status": "ok"})

  def test_health_db_error(self):
    """Test health view returns 503 status when database is down."""
    with patch("django.db.backends.utils.CursorWrapper.execute") as mock_execute:
      mock_execute.side_effect = DatabaseError("DB Down")
      response = self.client.get(reverse("health"))
      self.assertEqual(response.status_code, 503)
      self.assertEqual(response.json()["status"], "db_error")

  def test_health_redis_error(self):
    """Test health view returns 503 status when redis is down."""
    with patch("cm_main.views.views_general.redis_client") as mock_redis:
      mock_redis.ping.side_effect = redis.exceptions.ConnectionError("Redis Down")
      response = self.client.get(reverse("health"))
      self.assertEqual(response.status_code, 503)
      self.assertEqual(response.json()["status"], "redis_error")


class QHealthCheckTestCase(TestCase):
  @patch("cm_main.views.views_general.async_task")
  @patch("cm_main.views.views_general.result")
  def test_qhealth_ok(self, mock_result, mock_async_task):
    """Test qhealth view returns 200 status when everything is OK."""
    mock_async_task.return_value = "task_id"
    mock_result.return_value = {"status": "ok"}
    response = self.client.get(reverse("qhealth"))
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json(), {"status": "ok"})

  @patch("cm_main.views.views_general.async_task")
  @patch("cm_main.views.views_general.result")
  def test_qhealth_error(self, mock_result, mock_async_task):
    """Test qhealth view returns 503 status when task fails or returns error."""
    mock_async_task.return_value = "task_id"
    mock_result.return_value = {"status": "db_error"}
    response = self.client.get(reverse("qhealth"))
    self.assertEqual(response.status_code, 503)
    self.assertEqual(response.json()["status"], "db_error")

    mock_result.return_value = None
    response = self.client.get(reverse("qhealth"))
    self.assertEqual(response.status_code, 503)
