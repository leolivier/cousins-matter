from members.models import Member

from .base import MembersUITestBase


class ActivateAccountUITest(MembersUITestBase):
  """A superuser activates, from the member edit page, a member managed by someone else."""

  def test_superuser_activates_member_managed_by_someone_else(self):
    # Reassign Charlie's manager to Alice: otherwise Member.clean() auto-assigns
    # the superuser himself as manager and the button would show without the fix.
    self.member3.member_manager = self.member1
    self.member3.save()
    self.assertFalse(self.member3.is_active)

    self.login_and_goto_page("members:member_edit", kwargs={"username": self.member3.username})

    # activation requires a confirmation modal since issue 545
    activate_button = self.page.locator("button[hx-get$='/activate/']")
    activate_button.wait_for(state="visible")
    activate_button.click()
    modal_appeared = self.page.wait_for_selector(".modal-card", timeout=5000) is not None
    self.assertTrue(modal_appeared, "Activation confirmation modal should open")
    self.page.locator(".modal-card-foot button[type='submit']").click()

    # HX-Refresh reloads the edit page with a success flash
    self.page.wait_for_timeout(1000)
    self.assert_url_contains(f"/members/{self.member3.username}")
    self.assert_visible(".message.is-success", "Activation success message should be displayed")

    # Activated immediately: DB is the source of truth (no translated-text assert)
    member = Member.objects.get(username=self.member3.username)
    self.assertTrue(member.is_active, "Member should be active immediately after admin activation")
    self.assertIsNone(member.member_manager)
