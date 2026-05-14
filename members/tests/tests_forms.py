from datetime import date
from unittest.mock import MagicMock

from django.forms import ValidationError
from django.test import TestCase

from members.forms import FamilyUpdateForm, MemberRegistrationForm, MemberUpdateForm, validate_csv_extension
from members.models import Family, Member


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


class TestBirthdateFieldRequired(TestCase):
  """Tests for issue #379: birthdate field must be required in member forms."""

  def test_member_update_form_birthdate_required(self):
    """Test that birthdate field is required in MemberUpdateForm."""
    form = MemberUpdateForm()
    self.assertIn("birthdate", form.fields)
    self.assertTrue(form.fields["birthdate"].required, "birthdate field should be required in MemberUpdateForm")

  def test_member_update_form_invalid_without_birthdate(self):
    """Test that MemberUpdateForm is invalid when birthdate is missing."""
    data = {
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "privacy_consent": True,
    }
    form = MemberUpdateForm(data=data)
    self.assertFalse(form.is_valid())
    self.assertIn("birthdate", form.errors)

  def test_member_update_form_valid_with_birthdate(self):
    """Test that MemberUpdateForm is valid when birthdate is provided."""
    data = {
      "username": "testuser",
      "email": "test@example.com",
      "first_name": "Test",
      "last_name": "User",
      "birthdate": date(1990, 1, 1),
      "email_batch_frequency": "immediate",
      "privacy_consent": True,
    }
    form = MemberUpdateForm(data=data)
    self.assertTrue(form.is_valid(), f"Form should be valid with birthdate. Errors: {form.errors}")

  def test_member_registration_form_birthdate_required(self):
    """Test that birthdate field is required in MemberRegistrationForm."""
    form = MemberRegistrationForm()
    self.assertIn("birthdate", form.fields)
    self.assertTrue(form.fields["birthdate"].required, "birthdate field should be required in MemberRegistrationForm")

  def test_member_registration_form_invalid_without_birthdate(self):
    """Test that MemberRegistrationForm is invalid when birthdate is missing."""
    data = {
      "username": "newuser",
      "email": "new@example.com",
      "first_name": "New",
      "last_name": "User",
      "password1": "TestPass123!",
      "password2": "TestPass123!",
      "privacy_consent": True,
    }
    form = MemberRegistrationForm(data=data)
    self.assertFalse(form.is_valid())
    self.assertIn("birthdate", form.errors)

  def test_member_update_existing_member_with_birthdate_change(self):
    """Test that updating an existing member's birthdate works correctly."""
    # Create a test member
    member = Member.objects.create(
      username="existinguser",
      email="existing@example.com",
      first_name="Existing",
      last_name="User",
      birthdate=date(1985, 5, 15),
      privacy_consent=True,
    )

    try:
      # Update the birthdate
      new_birthdate = date(1986, 6, 16)
      data = {
        "username": member.username,
        "email": member.email,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "birthdate": new_birthdate,
        "email_batch_frequency": "immediate",
        "privacy_consent": True,
      }
      form = MemberUpdateForm(data=data, instance=member)
      self.assertTrue(form.is_valid(), f"Form should be valid. Errors: {form.errors}")

      updated_member = form.save()
      self.assertEqual(updated_member.birthdate, new_birthdate, "Birthdate should be updated to the new value")
    finally:
      member.delete()
