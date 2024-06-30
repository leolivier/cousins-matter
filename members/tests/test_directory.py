from django.http import FileResponse
from django.urls import reverse
from .tests_member_base import MemberTestCase
from ..views.views_directory import MembersDirectoryView, MembersPrintDirectoryView


class TestMemberDirectory(MemberTestCase):
  def setUp(self):
    super().setUp()
    self.members = []
    for _ in range(4):
      self.members.append(self.create_member())

  def tearDown(self):
    for member in self.members:
      member.delete()
    super().tearDown()

  def test_member_directory(self):

    response = self.client.get(reverse('members:directory'))
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, 'members/members/members_directory.html')
    self.assertIs(response.resolver_match.func.view_class, MembersDirectoryView)
    # print(response.content)
    for member in self.members:
        member_link = f'''
        <a class="button is-link is-light" href="{reverse("members:detail", args=[member.id])}">
          <strong>{member.get_full_name()}</strong>
        </a>
        '''
        self.assertContains(response, member_link, html=True)

  def test_pdf_generation(self):

    response = self.client.get(reverse('members:print_directory'))
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, MembersPrintDirectoryView)
    self.assertIs(response.__class__, FileResponse)
    self.assertEqual(response['Content-Type'], 'application/pdf')
