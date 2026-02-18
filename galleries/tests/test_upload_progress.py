from unittest.mock import patch
from django.urls import reverse
from galleries.tasks import ZipImport, ZIP_IMPORTS
from members.tests.tests_member_base import MemberTestCase


class UploadProgressViewTest(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.url_name = "galleries:upload_progress"
    self.task_group_id = "test_group_id"

    # Create a mock ZipImport object
    self.zimport = ZipImport(
      owner_id=self.member.id, root="/tmp/test_root", group=self.task_group_id, nbPhotos=10, nbGalleries=2
    )
    # Register the mock ZipImport
    ZIP_IMPORTS[self.task_group_id] = self.zimport

  def tearDown(self):
    # clean up global variable
    if self.task_group_id in ZIP_IMPORTS:
      del ZIP_IMPORTS[self.task_group_id]

  @patch("galleries.views.views_bulk.count_group")
  @patch("galleries.views.views_bulk.result_group")
  def test_upload_progress_in_progress(self, mock_result_group, mock_count_group):
    # Setup mocks for in-progress state
    mock_count_group.return_value = 5  # 5 out of 10 completed
    mock_result_group.return_value = [("photo1.jpg", []), (None, ["Some error"])]

    url = reverse(self.url_name, args=[self.task_group_id])
    response = self.client.get(url, HTTP_HX_REQUEST="true")

    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "cm_main/common/progress-bar.html")

    # Check context variables
    self.assertEqual(response.context["value"], 5)
    self.assertEqual(response.context["max"], 10)
    self.assertEqual(response.context["text"], "50%")
    self.assertIn("photo1.jpg", response.context["processed_objects"])
    self.assertIn("Some error", response.context["errors"])
    self.assertNotIn("success", response.context)  # Should not be success yet

  @patch("galleries.views.views_bulk.count_group")
  @patch("galleries.views.views_bulk.result_group")
  @patch("galleries.views.views_bulk.shutil.rmtree")
  def test_upload_progress_completed(self, mock_rmtree, mock_result_group, mock_count_group):
    # Setup mocks for completed state
    mock_count_group.return_value = 10  # 10 out of 10 completed
    mock_result_group.return_value = [("photo2.jpg", [])]

    url = reverse(self.url_name, args=[self.task_group_id])
    response = self.client.get(url, HTTP_HX_REQUEST="true")

    self.assertEqual(response.status_code, 200)

    # Check context variables
    self.assertEqual(response.context["value"], 10)
    self.assertEqual(response.context["max"], 10)
    self.assertEqual(response.context["text"], "100%")
    self.assertIn("photo2.jpg", response.context["processed_objects"])

    # Check success context
    self.assertIn("success", response.context)
    self.assertIn("back_url", response.context)
    self.assertIn("back_text", response.context)

    # Check cleanup - verify rmtree was called
    mock_rmtree.assert_called_once_with("/tmp/test_root")

    # Verify zimport is unregistered
    self.assertFalse(self.task_group_id in ZIP_IMPORTS)

  def test_upload_progress_not_found(self):
    # Test with a non-existent group ID
    url = reverse(self.url_name, args=["non_existent_id"])
    response = self.client.get(url, HTTP_HX_REQUEST="true")

    self.assertEqual(response.status_code, 404)
