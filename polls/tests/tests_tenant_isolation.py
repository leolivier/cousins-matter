"""Tenant-isolation tests for polls (TenantModel).

Proves ``Poll``/``Question``/``PollAnswer``/answers honor the
tenant-scoped manager — including the ``EventPlanner`` MTI child, which
must redeclare the scoped manager — plus tenant derivation from the
parent poll, ``unscoped`` escape hatch, and the default-tenant fallback.
"""

from django.test import TestCase

from members.tests.factories import MemberFactory
from polls.models import EventPlanner, Poll, PollAnswer, Question, YesNoAnswer
from polls.tests.factories import PollAnswerFactory, PollFactory, QuestionFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context


class PollTenantIsolationTests(TestCase):
  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name="A", slug="t-polls-a")
    cls.tenant_b = Tenant.objects.create(name="B", slug="t-polls-b")
    # tenant flows down the chain: factories derive it from the parent poll
    cls.poll_a = PollFactory(tenant=cls.tenant_a)
    cls.poll_b = PollFactory(tenant=cls.tenant_b)
    cls.question_a = QuestionFactory(poll=cls.poll_a)
    cls.question_b = QuestionFactory(poll=cls.poll_b)
    cls.vote_a = PollAnswerFactory(poll=cls.poll_a, member=cls.poll_a.owner, create_answers=True)
    cls.vote_b = PollAnswerFactory(poll=cls.poll_b, member=cls.poll_b.owner, create_answers=True)

  def setUp(self):
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)

  def test_queryset_isolation(self):
    with tenant_context(self.tenant_a):
      self.assertNotIn(self.poll_b.id, set(Poll.objects.values_list("id", flat=True)))
      self.assertIn(self.question_a.id, set(Question.objects.values_list("id", flat=True)))
      self.assertNotIn(self.question_b.id, set(Question.objects.values_list("id", flat=True)))
      self.assertEqual(set(PollAnswer.objects.values_list("id", flat=True)), {self.vote_a.id})
      self.assertEqual(
        set(YesNoAnswer.objects.values_list("id", flat=True)),
        set(self.vote_a.yesnoanswer_set.values_list("id", flat=True)),
      )

  def test_tenant_derived_from_parent(self):
    self.assertEqual(self.question_a.tenant_id, self.tenant_a.id)
    self.assertEqual(self.vote_a.tenant_id, self.tenant_a.id)
    self.assertEqual(self.vote_a.yesnoanswer_set.first().tenant_id, self.tenant_a.id)

  def test_eventplanner_mti_scoped(self):
    with tenant_context(self.tenant_b):
      planner = EventPlanner.objects.create(title="Planner", owner=self.poll_b.owner)
    self.assertEqual(planner.tenant_id, self.tenant_b.id)
    with tenant_context(self.tenant_a):
      self.assertNotIn(planner.id, set(EventPlanner.objects.values_list("id", flat=True)))

  def test_unscoped_sees_all(self):
    self.assertEqual(set(Poll.unscoped.values_list("id", flat=True)), {self.poll_a.id, self.poll_b.id})

  def test_save_without_tenant_falls_back_to_default(self):
    # e.g. a script creating a Poll outside any tenant_context: lands on default
    p = PollFactory.build(tenant=None, owner=MemberFactory())
    p.save()
    self.assertEqual(p.tenant.slug, "default")
