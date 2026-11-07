"""GDPR privacy consent gate tests.

Covers:
- the consent middleware: unconsented members are redirected to their profile until they consent
- the consent checkbox: only shown on forms where the member consents for themself (profile),
  never on managed-member creation or editing another member.
"""

from django.urls import reverse

from ..forms import MemberUpdateForm
from ..models import Member

from .tests_member_base import MemberTestCase, get_new_member_data, modify_member_data


class PrivacyGateTest(MemberTestCase):
  def get_unconsented_member(self):
    """creates an active member who has not consented to the privacy policy and logs it in."""
    data = get_new_member_data(privacy_consent=False)
    pwd = data["password"]
    member = Member.objects.create_member(**data, is_active=True)
    member.password = pwd  # keep unhashed password in memory for login
    self.created_members.append(member)
    self.client.logout()
    self.client.login(username=member.email, password=member.password)
    return member

  def test_unconsented_member_is_redirected_to_profile(self):
    self.get_unconsented_member()
    response = self.client.get(reverse("members:members"), follow=True)
    self.assertRedirects(response, reverse("members:profile"))
    self.assertContainsMessage(response, "warning", "You must accept the privacy policy to use this site.")

  def test_consented_member_is_not_redirected(self):
    self.assertTrue(self.member.privacy_consent)
    response = self.client.get(reverse("members:members"))
    self.assertEqual(response.status_code, 200)

  def test_profile_post_with_consent_unlocks_site(self):
    member = self.get_unconsented_member()
    profile_url = reverse("members:profile")
    self.assertEqual(self.client.get(profile_url).status_code, 200)
    data = modify_member_data(member)
    data["email"] = member.email  # keep email: changing it switches the view to email verification (no save)
    data["privacy_consent"] = True
    self.client.post(profile_url, data)
    member.refresh_from_db()
    self.assertTrue(member.privacy_consent)
    response = self.client.get(reverse("members:members"))
    self.assertEqual(response.status_code, 200)

  def test_logout_is_reachable_without_consent(self):
    self.get_unconsented_member()
    response = self.client.get(reverse("members:logout"))
    self.assertEqual(response.status_code, 302)  # redirected to login, not trapped on the gate
    self.assertRequestUserIsNotLogged()

  def test_privacy_field_only_on_profile_form(self):
    form = MemberUpdateForm()
    self.assertNotIn("privacy_consent", form.fields)
    form = MemberUpdateForm(is_profile=True)
    self.assertIn("privacy_consent", form.fields)
    self.assertTrue(form.fields["privacy_consent"].required)

  def test_managed_member_created_without_consent(self):
    # the creator may check the box: the value must not apply to the managed member
    data = get_new_member_data()
    data["privacy_consent"] = True
    response = self.client.get(reverse("members:create"))
    self.assertNotContains(response, 'name="privacy_consent"')
    self.client.post(reverse("members:create"), data)
    managed = Member.objects.filter(username=data["username"]).first()
    self.assertIsNotNone(managed)
    self.created_members.append(managed)
    self.assertFalse(managed.privacy_consent)
