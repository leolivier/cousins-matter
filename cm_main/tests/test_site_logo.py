import os

# import shutil
from django.conf import settings
from django.urls import reverse
from django.test import TestCase
from django.templatetags.static import static

from cousinsmatter.context_processors import override_settings
from cm_main.tests.test_protected_media import TestMediaResourceMixin


class TestSiteLogo(TestMediaResourceMixin, TestCase):
    # disable navbar cache for this test
    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    )
    def test_custom_logo(self):
        """test the custom site logo"""
        logo_basefilename = "test-logo.jpg"
        logo_target_path = os.path.join("public", logo_basefilename)
        logo_testresources_file = os.path.join(
            os.path.dirname(__file__), "resources", logo_basefilename
        )
        logo_url = f"{settings.PUBLIC_MEDIA_URL}{logo_basefilename}"

        current_logo_url = static(settings.SITE_LOGO)
        format = """<a class="navbar-item" href="/">
  <img src="%s" width="112" height="28">
</a>"""
        # check if the current logo is already set to the test logo
        if current_logo_url == logo_url:
            self.assertTrue(
                False, f"SITE_LOGO should not be set to {logo_url} for this test"
            )
        else:
            # test the current_logo
            response = self.client.get(reverse("cm_main:Home"), follow=True)
            self.assertContains(response, format % current_logo_url, html=True)

        logo_target_path = self.copy_test_resource(
            logo_testresources_file, logo_target_path
        )

        # override the settings SITE_LOGO
        with override_settings(SITE_LOGO=logo_url):
            response = self.client.get(reverse("cm_main:Home"), follow=True)
            self.assertContains(response, format % logo_url, html=True)

        # clean up
        self.clean_storage(logo_target_path)
