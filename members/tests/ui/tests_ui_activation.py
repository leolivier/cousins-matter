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

    activate_link = self.page.locator("a[href$='/activate/']")
    activate_link.wait_for(state="visible")
    activate_link.click()

    # The view redirects to the member detail page with a success flash
    self.page.wait_for_timeout(500)
    self.assert_url_contains(f"/members/{self.member3.username}")
    self.assert_visible(".message.is-success", "Activation success message should be displayed")

    # Activated immediately: DB is the source of truth (no translated-text assert)
    member = Member.objects.get(username=self.member3.username)
    self.assertTrue(member.is_active, "Member should be active immediately after admin activation")
    self.assertIsNone(member.member_manager)
