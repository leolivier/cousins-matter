from unittest.mock import MagicMock

from django.forms import ValidationError
from django.test import TestCase

from members.forms import FamilyUpdateForm, validate_csv_extension
from members.models import Family


class TestValidateCsvExtension(TestCase):
  """Tests for the validate_csv_extension function."""

  def test_valid_csv_extension(self):
    """Test that .csv files pass validation."""
    mock_file = MagicMock()
    mock_file.name = "members.csv"
    # Should not raise
    validate_csv_extension(mock_file)

  def test_invalid_extension(self):
    """Test that non-.csv files raise ValidationError."""
    mock_file = MagicMock()
    mock_file.name = "members.txt"
    with self.assertRaises(ValidationError):
      validate_csv_extension(mock_file)


class TestFamilyUpdateFormCleanName(TestCase):
  """Tests for FamilyUpdateForm.clean_name validation."""

  def test_empty_family_name(self):
    """Test that whitespace-only family name raises ValidationError."""
    family = Family.objects.create(name="TestFamilyForClean")
    try:
      form = FamilyUpdateForm(data={"name": "   "}, instance=family)
      self.assertFalse(form.is_valid())
      self.assertIn("name", form.errors)
    finally:
      family.delete()
