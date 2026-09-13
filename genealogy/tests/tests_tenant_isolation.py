"""Tenant-isolation tests genealogy (TenantModel).

Proves ``Person``/``Family`` honor the tenant-scoped manager — including
per-tenant ``gedcom_id`` uniqueness (two tenants may each import a GEDCOM
using ``@I1@``) — plus tenant derivation from the family partners,
``unscoped`` escape hatch, default-tenant fallback.
"""

from django.db import IntegrityError, transaction
from django.test import TestCase

from genealogy.models import Family, Person
from genealogy.tests.factories import FamilyFactory, PersonFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context


class GenealogyTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-gen-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-gen-b")
    cls.person_a = PersonFactory(tenant=cls.tenant_a, member=None, gedcom_id="@I1@")
    cls.person_b = PersonFactory(tenant=cls.tenant_b, member=None, gedcom_id="@I1@")
    # tenant flows up: a family belongs to its partners' tenant
    cls.family_a = FamilyFactory(partner1=cls.person_a)
    cls.family_b = FamilyFactory(partner1=cls.person_b)

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      self.assertNotIn(self.person_b.id, set(Person.objects.values_list("id", flat=True)))
      self.assertNotIn(self.family_b.id, set(Family.objects.values_list("id", flat=True)))
    with tenant_context(self.tenant_b):
      self.assertNotIn(self.person_a.id, set(Person.objects.values_list("id", flat=True)))
      self.assertNotIn(self.family_a.id, set(Family.objects.values_list("id", flat=True)))

  def test_tenant_assignment(self):
    self.assertEqual(self.person_a.tenant_id, self.tenant_a.id)
    self.assertEqual(self.family_a.tenant_id, self.tenant_a.id)
    self.assertEqual(self.family_a.partner1.tenant_id, self.tenant_a.id)

  def test_gedcom_id_unique_per_tenant(self):
    # Same GEDCOM id in two tenants is fine…
    self.assertEqual(self.person_a.gedcom_id, self.person_b.gedcom_id)
    # …but a duplicate inside one tenant is rejected by the constraint.
    with self.assertRaises(IntegrityError), transaction.atomic():
      PersonFactory(tenant=self.tenant_a, member=None, gedcom_id="@I1@")

  def test_unscoped(self):
    unscoped = set(Person.unscoped.values_list("id", flat=True))
    self.assertIn(self.person_a.id, unscoped)
    self.assertIn(self.person_b.id, unscoped)

  def test_save_without_tenant_falls_back_to_default(self):
    p = PersonFactory.build(tenant=None, member=None)
    p.save()
    self.assertEqual(p.tenant.slug, Tenant.get_default().slug)
