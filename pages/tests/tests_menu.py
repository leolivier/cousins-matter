from django.conf import settings
from django.urls import reverse

from cm_main.templatetags.cm_tags import icon

from cousinsmatter.context_processors import override_settings
from members.tests.tests_member_base import MemberTestCase
from ..models import FlatPage
from .test_base import BasePageTestCase, TestPageMixin


class TestDisplayPageMenu(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_only_superuser_can_create_pages(self):
    response = self.client.get(reverse("pages-edit:edit_list"))
    self.assertEqual(response.status_code, 403)
    page_data = {
      "url": settings.MENU_PAGE_URL_PREFIX + "/1rst-title33333/",
      "title": "first title",
      "content": "first content",
      "save": "true",
    }
    response = self.client.post(reverse("pages-edit:create"), page_data)
    self.assertEqual(response.status_code, 403)
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    response = self.client.post(reverse("pages-edit:create"), page_data, follow=True)
    self.assertEqual(response.status_code, 200)
    page = FlatPage.objects.get(url=page_data["url"])
    self.assertIsNotNone(page)
    self.client.login(username=self.member.username, password=self.member.password)  # now log back as a normal user
    page_data = {
      "url": settings.MENU_PAGE_URL_PREFIX + "/another-title33333/",
      "title": "another title",
      "content": "another content",
    }
    response = self.client.post(reverse("pages-edit:update", args=[page.id]), page_data)
    # self.print_response(response)
    self.assertEqual(response.status_code, 403)
    page.delete()

  # disable navbar cache for this test
  @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
  def test_display_page_menu(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    page_list_data = [
      {
        "url": settings.MENU_PAGE_URL_PREFIX + "/1rst-title/",
        "title": "first title",
        "content": "first content",
        "save": "true",
      },
      {
        "url": settings.MENU_PAGE_URL_PREFIX + "/level/2nd-title/",
        "title": "2nd title",
        "content": "2nd content",
        "save": "true",
      },
      {
        "url": settings.MENU_PAGE_URL_PREFIX + "/level/3rd-title/",
        "title": "3rd title",
        "content": "3rd content",
        "save": "true",
      },
    ]
    pages = [self._test_create_page(page_data) for page_data in page_list_data]
    response = self.client.get(reverse("pages-edit:edit_list"), follow=True)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    page_icon = icon("page", "is-small mr-3")
    level_icon = icon("page-level", "ml-0")
    self.assertContains(
      response,
      f"""
<a class="navbar-item" href="/{settings.PAGES_URL_PREFIX}{pages[0].url}">
  {page_icon}
  <span>{pages[0].title}</span>
</a>""",
      html=True,
    )
    self.assertContains(
      response,
      f"""
<div class="navbar-item has-dropdown is-hoverable">
  <p class="navbar-link">
    {level_icon}
    <span>level</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  </p>
  <div class="navbar-dropdown">
    <a class="navbar-item" href="/{settings.PAGES_URL_PREFIX}{pages[1].url}">
      {page_icon}
      <span>{pages[1].title}</span>
    </a>
    <a class="navbar-item" href="/{settings.PAGES_URL_PREFIX}{pages[2].url}">
      {page_icon}
      <span>{pages[2].title}</span>
    </a>
  </div>
</div>""",
      html=True,
    )

  def test_display_bad_page_menu(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    bad_page_data = {
      # url doesn't start with settings.MENU_PAGE_URL_PREFIX=>won't appear in the navbar
      "url": "/foo/1rst-title/",
      "title": "first title",
      "content": "first content",
      "save": "true",
    }

    bad_page = self._test_create_page(bad_page_data)
    response = self.client.get(reverse("pages-edit:edit_list"), follow=True)
    # print("response", response)
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(
      response,
      f'''
<a class="navbar-item" href="{bad_page.url}">
  {icon("page")}
  {bad_page.title}
</a>''',
      html=True,
    )
