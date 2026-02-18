from django.urls import reverse
from ..views.views_address import (
  ModalAddressCreateView,
  ModalAddressUpdateView,
)
from ..models import Address
from .tests_member_base import MemberTestCase

TEST_ADDR = {
  "number_and_street": "1 Avenue des Champs-Elysées",
  "city": "Paris",
  "zip_code": 75016,
  "complementary_info": "16eme",
  "country": "France",
}


def get_test_address():
  addr = TEST_ADDR.copy()
  TEST_ADDR["zip_code"] += 10
  return addr


class TestModalAddressView(MemberTestCase):
  def test_create_modal_address_view(self):
    """Tests that the modal address creation view works correctly."""
    cr_addr_url = reverse("members:modal_create_address")
    response = self.client.get(cr_addr_url)
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressCreateView)
    test_addr = get_test_address()
    response = self.client.post(cr_addr_url, test_addr, HTTP_HX_REQUEST="true")
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressCreateView)
    addr = Address.objects.filter(zip_code=test_addr["zip_code"]).first()
    self.assertIsNotNone(addr)
    self.assertContains(response, '<option value="' + str(addr.id) + '" selected>' + str(addr) + "</option>")

  def test_modify_modal_address_view(self):
    """Tests that the modal address update view works correctly."""
    # test get update
    addr = Address(**get_test_address())
    addr.save()
    self.assertIsNotNone(addr.id)
    ud_addr_url = reverse("members:modal_update_address", kwargs={"pk": addr.id})
    response = self.client.get(ud_addr_url)
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressUpdateView)
    # test post update
    test_addr = get_test_address()  # just modifies the zip code
    response = self.client.post(ud_addr_url, test_addr, HTTP_HX_REQUEST="true")
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressUpdateView)
    addr.refresh_from_db()
    self.assertContains(response, '<option value="' + str(addr.id) + '" selected>' + str(addr) + "</option>")
