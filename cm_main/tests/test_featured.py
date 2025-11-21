from django.urls import reverse
from django.test import override_settings
from django.utils.translation import gettext_lazy as _
from members.tests.tests_member_base import MemberTestCase
from cm_main.templatetags.cm_tags import icon

# NOTE: show birthday in home page is tested in test_homepage in pages tests


class TestFeaturedMixin(MemberTestCase):
    def build_url(self, url, name, icon_name, icon_classes="is-small mr-3"):
        "Helper method to build navigation URLs for testing."
        return f"""
<a class="navbar-item" href="{reverse(url)}">
  {icon(icon_name, icon_classes)} <span>{name}</span>
</a>
"""

    def setUp(self):
        "Initializes URLs for testing features."
        super().setUp()
        self.privchat_url = self.build_url(
            "chat:private_chat_rooms", _("Private Chat Rooms"), "chat"
        )
        self.pubchat_url = self.build_url(
            "chat:chat_rooms", _("Public Chat Rooms"), "chat"
        )
        self.galleries_url = self.build_url(
            "galleries:galleries", _("Galleries"), "galleries"
        )
        self.forums_url = self.build_url("forum:list", _("Forum"), "forum")
        self.troves_url = self.build_url("troves:list", _("Troves"), "troves")
        self.polls_url = self.build_url("polls:list_polls", _("Polls"), "vote")
        self.event_planners_url = self.build_url(
            "polls:list_event_planners", _("Event Planners"), "vote"
        )
        self.ads_url = self.build_url(
            "classified_ads:list", _("Classified Ads"), "classified-ads"
        )
        self.pages_url = self.build_url("pages-edit:tree", _("Pages"), "page-level")
        self.export_url = self.build_url(
            "members:select_members_to_export",
            _("Export Members as CSV"),
            "import-members",
        )


class TestFeaturedGalleries(TestFeaturedMixin):
    @override_settings(FEATURES_FLAGS={"show_galleries": False})
    def test_galleries_disabled(self):
        "Tests galleries are hidden when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.galleries_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_galleries": True})
    def test_galleries_enabled(self):
        "Tests galleries are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.galleries_url, html=True)


class TestFeaturedForums(TestFeaturedMixin):
    @override_settings(FEATURES_FLAGS={"show_forums": False})
    def test_forums_disabled(self):
        "Tests forums are hidden when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.forums_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_forums": True})
    def test_forums_enabled(self):
        "Tests forums are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.forums_url, html=True)


class TestFeaturedChats(TestFeaturedMixin):
    @override_settings(
        FEATURES_FLAGS={"show_private_chats": False, "show_public_chats": False}
    )
    def test_both_chats_disabled(self):
        "Tests both chats are hidden when both features are disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f"<span>{_('Chat')}</span>", html=True)
        self.assertNotContains(response, self.pubchat_url, html=True)
        self.assertNotContains(response, self.privchat_url, html=True)

    @override_settings(
        FEATURES_FLAGS={"show_private_chats": True, "show_public_chats": False}
    )
    def test_private_chats_enabled(self):
        "Tests private chats are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.privchat_url = self.build_url("chat:private_chat_rooms", _("Chat"), "chat")
        self.assertContains(response, self.privchat_url, html=True)
        self.pubchat_url = self.build_url(
            "chat:chat_rooms", _("Public Chat Rooms"), "chat"
        )
        self.assertNotContains(response, self.pubchat_url, html=True)
        self.pubchat_url = self.build_url("chat:chat_rooms", _("Chat"), "chat")
        self.assertNotContains(response, self.pubchat_url, html=True)

    @override_settings(
        FEATURES_FLAGS={"show_private_chats": False, "show_public_chats": True}
    )
    def test_public_chats_enabled(self):
        "Tests public chats are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.pubchat_url = self.build_url("chat:chat_rooms", _("Chat"), "chat")
        self.assertContains(response, self.pubchat_url, html=True)
        self.privchat_url = self.build_url("chat:private_chat_rooms", _("Chat"), "chat")
        self.assertNotContains(response, self.privchat_url, html=True)
        self.privchat_url = self.build_url("chat:private_chat_rooms", _("Chat"), "chat")
        self.assertNotContains(response, self.privchat_url, html=True)

    @override_settings(
        FEATURES_FLAGS={"show_private_chats": True, "show_public_chats": True}
    )
    def test_both_chats_enabled(self):
        "Tests both chats are visible when both features are enabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.privchat_url = self.build_url(
            "chat:private_chat_rooms", _("Private Chat Rooms"), "chat"
        )
        self.assertContains(response, self.privchat_url, html=True)
        self.pubchat_url = self.build_url(
            "chat:chat_rooms", _("Public Chat Rooms"), "chat"
        )
        self.assertContains(response, self.pubchat_url, html=True)


class TestFeaturedClassifiedAds(TestFeaturedMixin):
    @override_settings(FEATURES_FLAGS={"show_classified_ads": False})
    def test_classified_ads_disabled(self):
        "Tests classified ads are hidden when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.ads_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_classified_ads": True})
    def test_classified_ads_enabled(self):
        "Tests classified ads are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ads_url, html=True)


class TestFeaturedPolls(TestFeaturedMixin):
    @override_settings(
        FEATURES_FLAGS={"show_polls": False, "show_event_planners": False}
    )
    def test_polls_and_planners_disabled(self):
        "Tests polls and event planners are hidden when both features are disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.polls_url, html=True)
        self.assertNotContains(response, self.event_planners_url, html=True)

    @override_settings(
        FEATURES_FLAGS={"show_polls": True, "show_event_planners": False}
    )
    def test_polls_enabled_only(self):
        "Tests only polls are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.polls_url, html=True)
        self.assertNotContains(response, self.event_planners_url, html=True)
        response = self.client.get(reverse("polls:list_polls"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.polls_url, html=True)
        self.assertNotContains(response, self.event_planners_url, html=True)

    @override_settings(
        FEATURES_FLAGS={"show_event_planners": True, "show_polls": False}
    )
    def test_event_planners_enabled_only(self):
        "Tests only event planners are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_planners_url, html=True)
        self.assertNotContains(response, self.polls_url, html=True)
        response = self.client.get(reverse("polls:list_event_planners"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event_planners_url, html=True)
        self.assertNotContains(response, self.polls_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_polls": True, "show_event_planners": True})
    def test_polls_and_event_planners_enabled(self):
        "Tests both polls and event planners are visible when both features are enabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.polls_url, html=True)
        response = self.client.get(reverse("polls:list_polls"))
        self.assertEqual(response.status_code, 200)
        lep_url = reverse("polls:list_event_planners")
        self.assertContains(
            response, f"""<a  href="{lep_url}">{_('Event planners')}</a>""", html=True
        )
        response = self.client.get(reverse("polls:list_event_planners"))
        self.assertEqual(response.status_code, 200)
        poll_url = reverse("polls:list_polls")
        self.assertContains(
            response, f"""<a  href="{poll_url}">{_('Polls')}</a>""", html=True
        )


class TestFeaturedTreasures(TestFeaturedMixin):
    @override_settings(FEATURES_FLAGS={"show_treasures": True})
    def test_treasures_enabled(self):
        "Tests treasures are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.troves_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_treasures": False})
    def test_treasures_disabled(self):
        "Tests treasures are hidden when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.troves_url, html=True)


class TestFeaturedExportMembers(TestFeaturedMixin):
    @override_settings(FEATURES_FLAGS={"show_export_members": True})
    def test_export_members_enabled(self):
        "Tests export members is visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.export_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_export_members": False})
    def test_export_members_disabled(self):
        "Tests export members is hidden when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.export_url, html=True)


class TestFeaturedPages(TestFeaturedMixin):
    @override_settings(FEATURES_FLAGS={"show_pages": True})
    def test_pages_enabled(self):
        "Tests pages are visible when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pages_url, html=True)

    @override_settings(FEATURES_FLAGS={"show_pages": False})
    def test_pages_disabled(self):
        "Tests pages are hidden when feature is disabled in settings."
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.pages_url, html=True)
