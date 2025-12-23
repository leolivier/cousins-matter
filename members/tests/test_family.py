from django.urls import reverse
from ..views.views_family import (
    FamilyCreateView,
    FamilyUpdateView,
    FamilyDetailView,
    ModalFamilyCreateView,
    ModalFamilyUpdateView,
)
from ..models import Family
from .tests_member_base import MemberTestCase

FAMILY_COUNT = 0


def get_test_family(parent=None):
    global FAMILY_COUNT
    family = {"name": f"The family #{FAMILY_COUNT}"}
    if parent:
        family["parent"] = parent
    FAMILY_COUNT += 1
    return family


class TestFamily(MemberTestCase):
    def test_create_and_modify_family(self):
        """Tests creating and modifying a family with its members."""
        # test create
        root_family = Family(**get_test_family())
        root_family.save()
        f_data = get_test_family(root_family)
        family = Family(**f_data)
        family.save()
        self.member.family = family
        self.member.save()
        self.assertEqual(Family.objects.get(name=f_data["name"]), self.member.family)
        self.assertEqual(self.member.family.parent, root_family)
        # test modify
        root_family.name = "My Very Big Family"
        root_family.save()
        self.assertEqual(self.member.family.parent.name, "My Very Big Family")


class TestFamilyView(MemberTestCase):
    def test_create_family_view(self):
        """Tests that the family creation view works correctly."""
        cr_family_url = reverse("members:create_family")
        response = self.client.get(cr_family_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "members/family/family_form.html")
        self.assertIs(response.resolver_match.func.view_class, FamilyCreateView)
        test_family = get_test_family()
        response = self.client.post(cr_family_url, test_family, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Family.objects.filter(name=test_family["name"]).exists())

    def test_modify_family_view(self):
        """Tests that the family update view works correctly."""
        family = Family(**get_test_family())
        family.save()
        self.assertIsNotNone(family.id)
        ud_family_url = reverse("members:update_family", kwargs={"pk": family.id})
        response = self.client.get(ud_family_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "members/family/family_form.html")
        self.assertIs(response.resolver_match.func.view_class, FamilyUpdateView)
        test_family = get_test_family()
        response = self.client.post(ud_family_url, test_family, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func.view_class, FamilyDetailView)
        family.refresh_from_db()
        self.assertEqual(family.name, str(test_family["name"]))


class TestModalFamilyView(MemberTestCase):
    def test_modal_family_create_view(self):
        """Tests family creation via modal view."""
        cr_family_url = reverse("members:modal_create_family")
        response = self.client.get(cr_family_url)
        self.assertEqual(response.status_code, 200)
        # actually does not used this form directly as it is included in a master one
        # self.assertTemplateUsed(response, 'members/modal_form.html')
        self.assertIs(response.resolver_match.func.view_class, ModalFamilyCreateView)
        test_family = get_test_family()
        response = self.client.post(
            cr_family_url, test_family, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func.view_class, ModalFamilyCreateView)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        family = Family.objects.filter(name=test_family["name"]).first()
        self.assertIsNotNone(family)
        self.assertJSONEqual(
            response.content.decode(),
            {
                "family_id": family.id,
                "family_name": str(family),
                "parent_family_id": family.parent.id if family.parent else "",
            },
        )
        # pprint(vars(response))

    def test_modify_modal_family_view(self):
        """Tests family update via modal view."""
        # test get update
        family = Family(**get_test_family())
        family.save()
        self.assertIsNotNone(family.id)
        ud_addr_url = reverse("members:modal_update_family", kwargs={"pk": family.id})
        response = self.client.get(ud_addr_url)
        self.assertEqual(response.status_code, 200)
        # actually does not used this form directmy as it is included in a master one
        # self.assertTemplateUsed(response, 'members/modal_form.html')
        self.assertIs(response.resolver_match.func.view_class, ModalFamilyUpdateView)
        # test post update
        test_addr = get_test_family()  # modifies the name
        response = self.client.post(
            ud_addr_url, test_addr, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIs(response.resolver_match.func.view_class, ModalFamilyUpdateView)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        family.refresh_from_db()
        self.assertJSONEqual(
            response.content.decode(),
            {
                "family_id": family.id,
                "family_name": str(family),
                "parent_family_id": family.parent.id if family.parent else "",
            },
        )
        # pprint(vars(response))
