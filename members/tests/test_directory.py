from django.http import FileResponse
from django.urls import reverse
from .tests_member_base import MemberTestCase
from ..views.views_directory import MembersDirectoryView, MembersPrintDirectoryView


class TestMemberDirectory(MemberTestCase):
    def setUp(self):
        """Initializes test data for member directory."""
        super().setUp()
        for _ in range(4):
            self.create_member()

    def test_member_directory(self):
        """Tests that the member directory displays correctly with all visible members."""
        response = self.client.get(reverse("members:directory"), follow=True)
        # self.print_response(response)
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func.view_class, MembersDirectoryView)
        self.assertTemplateUsed(response, "members/members/members_directory.html")
        for member in self.created_members:
            member_link = f"""
        <a class="button is-link is-light" href="{reverse("members:detail", args=[member.id])}">
          <strong>{member.full_name}</strong>
        </a>
        """
            self.assertContains(response, member_link, html=True)

    def test_pdf_generation(self):
        """Tests that PDF generation for the member directory works correctly."""
        response = self.client.get(reverse("members:print_directory"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIs(
            response.resolver_match.func.view_class, MembersPrintDirectoryView
        )
        self.assertIs(response.__class__, FileResponse)
        self.assertEqual(response["Content-Type"], "application/pdf")
