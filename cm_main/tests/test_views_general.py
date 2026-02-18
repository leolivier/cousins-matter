from django.test import TestCase
from django.urls import reverse
from django.db.utils import DatabaseError
from unittest.mock import patch
import redis
from members.tests.tests_member_base import MemberTestCase
from cm_main.forms import PasswordResetForm


class GeneralViewsTestCase(MemberTestCase):
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

  def test_password_reset_post(self):
    """Test that PasswordResetForm.save is called and works."""
    # We need to test the save method which is called during POST
    response = self.client.post(reverse("reset_password"), {"email": self.member.email}, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/login/password_reset_done.html")

  def test_download_protected_media_not_found(self):
    """Test that download_protected_media raises 404 if file not found."""
    # Line 68
    response = self.client.get(reverse("get_protected_media", args=["non_existent_file.jpg"]))
    self.assertEqual(response.status_code, 404)

  def test_download_protected_media_not_modified(self):
    """Test that download_protected_media returns 304 if ETag matches."""
    # Line 58
    from hashlib import blake2b

    media = "test_file.jpg"
    hasher = blake2b()
    tbh = bytes(f"{self.member.username}@{media}", "utf-8")
    hasher.update(tbh)
    media_etag = hasher.hexdigest()

    response = self.client.get(reverse("get_protected_media", args=[media]), HTTP_IF_NONE_MATCH=media_etag)
    self.assertEqual(response.status_code, 304)

  @patch("cm_main.views.views_general.default_storage.open")
  def test_download_protected_media_error(self, mock_open):
    """Test that download_protected_media raises 404 on general exception."""
    # Line 70
    mock_open.side_effect = Exception("General Error")
    response = self.client.get(reverse("get_protected_media", args=["some_file.jpg"]))
    self.assertEqual(response.status_code, 404)

  def test_send_zipfile(self):
    """Test that send_zipfile works."""
    from cm_main.views.views_general import send_zipfile
    from members.tests.tests_member_base import get_fake_request

    request = get_fake_request()
    response = send_zipfile(request)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response["Content-Type"], "application/zip")


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
