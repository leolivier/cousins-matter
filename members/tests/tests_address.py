from django.urls import reverse
from ..views.views_address import (
  AddressCreateView,
  AddressUpdateView,
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


class TestAddress(MemberTestCase):
  def test_create_and_modify_address(self):
    """Tests that the address creation and modification views work correctly."""
    # test create
    addr = Address(**get_test_address())
    addr.save()
    self.member.address = addr
    self.member.save()
    self.assertEqual(
      Address.objects.get(number_and_street="1 Avenue des Champs-Elysées"),
      self.member.address,
    )
    # test modify
    addr.number_and_street = "2 Avenue des Champs-Elysées"
    addr.save()
    self.assertEqual(self.member.address.number_and_street, "2 Avenue des Champs-Elysées")


class TestAddressView(MemberTestCase):
  def test_create_address_view(self):
    """Tests that the address creation view works correctly."""
    cr_addr_url = reverse("members:create_address")
    response = self.client.get(cr_addr_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/address/address_form.html")
    self.assertIs(response.resolver_match.func.view_class, AddressCreateView)
    test_addr = get_test_address()
    response = self.client.post(cr_addr_url, test_addr, follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertTrue(Address.objects.filter(zip_code=test_addr["zip_code"]).exists())

  def test_modify_address_view(self):
    """Tests that the address update view works correctly."""
    addr = Address(**get_test_address())
    addr.save()
    self.assertIsNotNone(addr.id)
    ud_addr_url = reverse("members:update_address", kwargs={"pk": addr.id})
    response = self.client.get(ud_addr_url)
    self.assertEqual(response.status_code, 200)
    self.assertTemplateUsed(response, "members/address/address_form.html")
    self.assertIs(response.resolver_match.func.view_class, AddressUpdateView)
    test_addr = get_test_address()
    response = self.client.post(ud_addr_url, test_addr, follow=True)
    self.assertEqual(response.status_code, 200)
    addr.refresh_from_db()
    self.assertEqual(addr.zip_code, str(test_addr["zip_code"]))


class TestModalAddressView(MemberTestCase):
  def test_create_modal_address_view(self):
    """Tests that the modal address creation view works correctly."""
    cr_addr_url = reverse("members:modal_create_address")
    response = self.client.get(cr_addr_url)
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressCreateView)
    test_addr = get_test_address()
    response = self.client.post(cr_addr_url, test_addr, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressCreateView)
    self.assertEqual(response.headers["Content-Type"], "application/json")
    addr = Address.objects.filter(zip_code=test_addr["zip_code"]).first()
    self.assertIsNotNone(addr)
    self.assertJSONEqual(
      response.content.decode(),
      {
        "address_id": addr.id,
        "number_and_street": addr.number_and_street,
        "complementary_info": addr.complementary_info,
        "zip_code": addr.zip_code,
        "city": addr.city,
        "country": addr.country,
        "address_str": str(addr),
      },
    )
    # pprint(vars(response))

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
    response = self.client.post(ud_addr_url, test_addr, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    self.assertEqual(response.status_code, 200)
    self.assertIs(response.resolver_match.func.view_class, ModalAddressUpdateView)
    self.assertEqual(response.headers["Content-Type"], "application/json")
    addr.refresh_from_db()
    self.assertJSONEqual(
      response.content.decode(),
      {
        "address_id": addr.id,
        "number_and_street": addr.number_and_street,
        "complementary_info": addr.complementary_info,
        "zip_code": addr.zip_code,
        "city": addr.city,
        "country": addr.country,
        "address_str": str(addr),
      },
    )
    # print(response.content.decode())
