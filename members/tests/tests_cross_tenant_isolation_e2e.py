"""Automated version of the cross-tenant isolation scenario.

Mirrors ``docs/flows/cross-tenant-isolation.md`` at the HTTP level: two
families (tenants) seed the same marker content in every app, then each
family's browser probes the other family's lists, objects, members, chat
rooms, media, deactivation and superuser visibility.

The per-app ``tests_tenant_isolation.py`` modules already prove the ORM
layer; this module is the browser-level mirror described in the flow doc:
real sessions, real slugs, real URLs.

Must run with multi-tenancy on (``make test-mt``), since the family URLconf
and the tenant middleware's scoping only exist in that mode::

    make test-mt t=members.tests.tests_cross_tenant_isolation_e2e

or run ``scripts/tests/run_cross_tenant_isolation_e2e.sh``.
"""

from django.conf import settings
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse

from chat.models import PrivateChatRoom
from chat.tests.factories import ChatMessageFactory, ChatRoomFactory
from classified_ads.tests.factories import ClassifiedAdFactory
from forum.tests.factories import MessageFactory, PostFactory
from galleries.tests.factories import GalleryFactory, PhotoFactory
from genealogy.tests.factories import PersonFactory
from members.models import Member
from pages.tests.factories import FlatPageFactory
from polls.tests.factories import PollFactory
from tenants.models import Tenant
from tenants.scoping import set_current_tenant, tenant_context
from troves.tests.factories import TroveFactory

_PWD = "pw-12345-Aa"

FAMILY_A_NAME = "Isolation Family IFA"
FAMILY_A_SLUG = "isolation-family-ifa"
FAMILY_B_NAME = "Isolation Family IFB"
FAMILY_B_SLUG = "isolation-family-ifb"


def _make_member(tenant, username, first_name, role=Member.Role.MEMBER):
  with tenant_context(tenant):
    return Member.objects.create_member(
      username=username,
      password=_PWD,
      email=f"{username}@example.com",
      first_name=first_name,
      last_name="Isolation",
      is_active=True,
      role=role,
      privacy_consent=True,  # these tests exercise isolation, not the consent gate
    )


class CrossTenantIsolationE2ETests(TestCase):
  """Phases 1-7 of the cross-tenant isolation flow, plus its pass criteria."""

  @classmethod
  def setUpTestData(cls):
    cls.tenant_a = Tenant.objects.create(name=FAMILY_A_NAME, slug=FAMILY_A_SLUG)
    cls.tenant_b = Tenant.objects.create(name=FAMILY_B_NAME, slug=FAMILY_B_SLUG)

    cls.nora = _make_member(cls.tenant_a, "iso_nora", "Nora", Member.Role.ADMIN)
    cls.hugo = _make_member(cls.tenant_a, "iso_hugo", "Hugo")
    cls.ira = _make_member(cls.tenant_b, "iso_ira", "Ira", Member.Role.ADMIN)
    cls.lena = _make_member(cls.tenant_b, "iso_lena", "Lena")

    # --- family A marker content ------------------------------------------
    # fixtures are created inside tenant_context so model validation (e.g. the
    # root-gallery name check) only sees the tenant being seeded
    with tenant_context(cls.tenant_a):
      message_a = MessageFactory(tenant=cls.tenant_a, author=cls.hugo)
      cls.post_a = PostFactory(tenant=cls.tenant_a, title="ETA secret recipe", first_message=message_a, create_thread=False)
      cls.gallery_a = GalleryFactory(
        tenant=cls.tenant_a, name="Reunion", owner=cls.hugo, create_photos=False, create_subgalleries=False
      )
      cls.photo_a = PhotoFactory(tenant=cls.tenant_a, gallery=cls.gallery_a, uploaded_by=cls.hugo, name="ETA photo")
      cls.room_a = ChatRoomFactory(tenant=cls.tenant_a, name="Lounge", create_messages=False)
      cls.chat_a = ChatMessageFactory(tenant=cls.tenant_a, room=cls.room_a, member=cls.hugo, content="ETA lounge message")
      cls.private_a = PrivateChatRoom.objects.create(tenant=cls.tenant_a, name="ETA private")
      cls.private_a.followers.add(cls.hugo)
      cls.poll_a = PollFactory(tenant=cls.tenant_a, title="ETA picnic", owner=cls.hugo)
      cls.person_a = PersonFactory(tenant=cls.tenant_a, member=cls.hugo, first_name="Marcus", last_name="ETA")
      cls.trove_a = TroveFactory(tenant=cls.tenant_a, title="ETA treasury", owner=cls.hugo)
      cls.ad_a = ClassifiedAdFactory(tenant=cls.tenant_a, title="ETA bike", owner=cls.hugo, create_photos=False)
      cls.page_a = FlatPageFactory(tenant=cls.tenant_a, url="/rules/", title="ETA rules")

    # --- family B marker content (same names/slugs where the doc asks) ----
    with tenant_context(cls.tenant_b):
      message_b = MessageFactory(tenant=cls.tenant_b, author=cls.lena)
      cls.post_b = PostFactory(tenant=cls.tenant_b, title="IFB secret recipe", first_message=message_b, create_thread=False)
      cls.gallery_b = GalleryFactory(
        tenant=cls.tenant_b, name="Reunion", owner=cls.lena, create_photos=False, create_subgalleries=False
      )
      cls.photo_b = PhotoFactory(tenant=cls.tenant_b, gallery=cls.gallery_b, uploaded_by=cls.lena, name="IFB photo")
      cls.room_b = ChatRoomFactory(tenant=cls.tenant_b, name="Lounge", create_messages=False)
      cls.chat_b = ChatMessageFactory(tenant=cls.tenant_b, room=cls.room_b, member=cls.lena, content="IFB lounge message")
      cls.poll_b = PollFactory(tenant=cls.tenant_b, title="IFB picnic", owner=cls.lena)
      cls.person_b = PersonFactory(tenant=cls.tenant_b, member=cls.lena, first_name="Marcus", last_name="IFB")
      cls.trove_b = TroveFactory(tenant=cls.tenant_b, title="IFB treasury", owner=cls.lena)
      cls.ad_b = ClassifiedAdFactory(tenant=cls.tenant_b, title="IFB bike", owner=cls.lena, create_photos=False)
      cls.page_b = FlatPageFactory(tenant=cls.tenant_b, url="/rules/", title="IFB rules")

  def setUp(self):
    if not settings.MULTI_TENANT_ENABLED:
      self.skipTest("MULTI_TENANT_ENABLED is off: /tenants/ is not mounted")
    set_current_tenant(None)

  def tearDown(self):
    set_current_tenant(None)
    super().tearDown()

  # -- helpers -------------------------------------------------------------

  def _assert_denied(self, url, **kwargs):
    """A cross-family access must not serve the other family's data.

    The flow doc accepts 404, 403 or a redirect as a deny; a 200 rendering
    the other family's marker, or a 500, is a failure.
    """
    response = self.client.get(url, **kwargs)
    self.assertIn(response.status_code, (302, 403, 404), f"{url} answered {response.status_code}")
    self.assertNotContains(response, "IFB", status_code=response.status_code)

  def _assert_own_list(self, url, own_marker, other_marker, **kwargs):
    response = self.client.get(url, **kwargs)
    self.assertEqual(response.status_code, 200, url)
    self.assertContains(response, own_marker)
    self.assertNotContains(response, other_marker)
    return response

  def _assert_own_chat_rooms(self, own_room, other_room):
    # the chat list shows only room names/message counts, and both tenants
    # own a "Lounge": compare the listed pks instead of a text marker
    response = self.client.get(reverse("chat:chat_rooms"))
    self.assertEqual(response.status_code, 200)
    self.assertEqual([room.pk for room in response.context["page"]], [own_room.pk])
    self.assertNotEqual(own_room.pk, other_room.pk)

  # -- Phase 1/2 - list scoping -------------------------------------------

  def test_01_family_a_lists_show_only_family_a(self):
    self.client.force_login(self.nora)
    self._assert_own_list(reverse("forum:list"), "ETA secret recipe", "IFB secret recipe")
    self._assert_own_chat_rooms(self.room_a, self.room_b)
    self._assert_own_list(reverse("galleries:galleries"), "Reunion", "IFB photo")
    self._assert_own_list(reverse("polls:all_polls"), "ETA picnic", "IFB picnic")
    self._assert_own_list(reverse("genealogy:person_list"), "ETA", "IFB")
    self._assert_own_list(reverse("troves:list"), "ETA treasury", "IFB treasury")
    self._assert_own_list(reverse("classified_ads:list"), "ETA bike", "IFB bike")
    self._assert_own_list(reverse("pages-edit:edit_list"), "ETA rules", "IFB rules")
    self._assert_own_list(reverse("members:members"), "Nora", "Lena")

  def test_02_family_b_lists_show_only_family_b(self):
    self.client.force_login(self.lena)
    self._assert_own_list(reverse("forum:list"), "IFB secret recipe", "ETA secret recipe")
    self._assert_own_chat_rooms(self.room_b, self.room_a)
    self._assert_own_list(reverse("galleries:galleries"), "Reunion", "ETA photo")
    self._assert_own_list(reverse("polls:all_polls"), "IFB picnic", "ETA picnic")
    self._assert_own_list(reverse("genealogy:person_list"), "IFB", "ETA")
    self._assert_own_list(reverse("troves:list"), "IFB treasury", "ETA treasury")
    self._assert_own_list(reverse("classified_ads:list"), "IFB bike", "ETA bike")
    self._assert_own_list(reverse("members:members"), "Lena", "Nora")
    # the page admin list is tenant-admin only: check it as family B's admin
    self.client.force_login(self.ira)
    self._assert_own_list(reverse("pages-edit:edit_list"), "IFB rules", "ETA rules")

  # -- Phase 2 - direct object access by pk/slug ---------------------------

  def test_03_direct_object_access_by_pk_is_denied(self):
    self.client.force_login(self.nora)
    for url in (
      reverse("forum:display", args=[self.post_b.pk]),
      reverse("forum:edit", args=[self.post_b.pk]),
      reverse("galleries:photo", args=[self.photo_b.pk]),
      reverse("galleries:edit_photo", args=[self.photo_b.pk]),
      reverse("polls:poll_detail", args=[self.poll_b.pk]),
      reverse("polls:update_poll", args=[self.poll_b.pk]),
      reverse("genealogy:person_detail", args=[self.person_b.pk]),
      reverse("genealogy:person_update", args=[self.person_b.pk]),
      reverse("troves:detail", args=[self.trove_b.pk]),
      reverse("troves:update", args=[self.trove_b.pk]),
      reverse("classified_ads:detail", args=[self.ad_b.pk]),
      reverse("classified_ads:update", args=[self.ad_b.pk]),
      reverse("pages-edit:update", args=[self.page_b.pk]),
    ):
      self._assert_denied(url)

    # the identically-named gallery slug must land on family A's gallery
    response = self.client.get(reverse("galleries:detail", args=[self.gallery_b.slug]))
    self.assertContains(response, "ETA photo")
    self.assertNotContains(response, "IFB photo")

  # -- Phase 3 - member lookups -------------------------------------------

  def test_04_member_lookups_never_cross_families(self):
    self.client.force_login(self.nora)
    for url in (
      reverse("members:detail", args=[self.lena.username]),
      reverse("members:member_edit", args=[self.lena.username]),
      reverse("members:toggle_follow", args=[self.lena.username]),
    ):
      self._assert_denied(url)
    # the delete confirmation view is HTMX-only
    self._assert_denied(reverse("members:delete", args=[self.lena.username]), HTTP_HX_REQUEST="true")

    search = self.client.get(reverse("members:search_members"), {"search": "lena"}, HTTP_HX_REQUEST="true")
    self.assertEqual(search.status_code, 200)
    self.assertNotContains(search, "Lena")
    search = self.client.get(reverse("members:search_members"), {"search": "ira"}, HTTP_HX_REQUEST="true")
    self.assertEqual(search.status_code, 200)
    self.assertNotContains(search, "Ira")

  # -- Phase 4 - chat specifics -------------------------------------------

  def test_05_chat_rooms_share_name_but_not_messages(self):
    self.client.force_login(self.nora)
    room = self.client.get(reverse("chat:room", args=[self.room_a.slug]))
    self.assertEqual(room.status_code, 200)
    self.assertContains(room, "ETA lounge message")
    self.assertNotContains(room, "IFB lounge message")
    # private-room recipient autocomplete proposes only family A members
    search = self.client.get(
      reverse("chat:search_private_members", args=[self.private_a.slug]), {"q": "lena"}, HTTP_HX_REQUEST="true"
    )
    self.assertEqual(search.status_code, 200)
    self.assertNotContains(search, "Lena")
    search = self.client.get(
      reverse("chat:search_private_members", args=[self.private_a.slug]), {"q": "hugo"}, HTTP_HX_REQUEST="true"
    )
    self.assertContains(search, "Hugo")

  # -- Phase 5 - protected media -----------------------------------------

  def test_06_protected_media_is_tenant_gated(self):
    """Media files are login-gated and tenant-gated (first path segment = tenant slug)."""
    self.assertTrue(self.photo_b.image.name.startswith(f"{self.tenant_b.slug}/"))
    self.assertTrue(default_storage.exists(self.photo_b.image.name))
    url = reverse("get_protected_media", args=[self.photo_b.image.name])
    # anonymous access is refused
    self.assertEqual(self.client.get(url).status_code, 302)
    # a member of the other family must not get the file
    self.client.force_login(self.nora)
    self.assertEqual(self.client.get(url).status_code, 404)
    # family B's own member still gets it
    self.client.force_login(self.lena)
    self.assertEqual(self.client.get(url).status_code, 200)

  # -- Phase 6 - deactivated family ---------------------------------------

  def test_07_deactivated_family_locks_its_members_out(self):
    self.tenant_b.is_active = False
    self.tenant_b.save(update_fields=["is_active"])

    self.client.force_login(self.lena)
    response = self.client.get(reverse("members:members"))
    self.assertEqual(response.status_code, 302)
    self.assertIn(reverse("members:login"), response["Location"])
    self.assertFalse(self.client.session.get("_auth_user_id"))

    # family A is untouched
    self.client.force_login(self.nora)
    self.assertEqual(self.client.get(reverse("members:members")).status_code, 200)

    # the deactivated family's public pages are gone
    self.assertEqual(self.client.get(reverse("tenant-home", args=[FAMILY_B_SLUG])).status_code, 404)
    self.assertEqual(self.client.get(reverse("tenant-join", args=[FAMILY_B_SLUG])).status_code, 404)

  # -- Phase 7 - platform superuser is unscoped ---------------------------

  def test_08_platform_superuser_crosses_families_by_design(self):
    superuser = Member.objects.create_superuser(
      username="iso_su",
      email="iso_su@example.com",
      password=_PWD,
      first_name="Platform",
      last_name="Admin",
      privacy_consent=True,  # skip the GDPR profile gate
    )
    self.client.force_login(superuser)
    families = self.client.get(reverse("tenants:list"))
    self.assertEqual(families.status_code, 200)
    self.assertContains(families, FAMILY_A_NAME)
    self.assertContains(families, FAMILY_B_NAME)
    admin = self.client.get("/admin/members/member/")
    self.assertEqual(admin.status_code, 200)
    self.assertContains(admin, "Lena")
    self.assertContains(admin, "Hugo")

    # the cross-family visibility stays confined to the superuser session
    self.client.force_login(self.nora)
    self.assertNotContains(self.client.get(reverse("members:members")), "Lena")
