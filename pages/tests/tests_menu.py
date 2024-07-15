from django.urls import reverse
from django.contrib.flatpages.models import FlatPage

from cm_main.templatetags.cm_tags import icon

from members.tests.tests_member_base import MemberTestCase
from pages.utils import flatpage_url
from .test_base import BasePageTestCase, TestPageMixin


class TestDisplayPageMenu(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_only_superuser_can_create_pages(self):
    response = self.client.get(reverse('pages-edit:list'))
    self.assertEqual(response.status_code, 403)
    page_data = {
        'url': '/publish/1rst-title33333',
        'title': 'first title',
        'content': 'first content',
      }
    response = self.client.post(reverse("pages-edit:create"), page_data)
    self.assertEqual(response.status_code, 403)
    self.superuser_login()  # only superuser can create pages
    response = self.client.post(reverse("pages-edit:create"), page_data)
    self.assertEqual(response.status_code, 200)
    page = FlatPage.objects.get(url=page_data['url'])
    self.assertIsNotNone(page)
    self.login()  # now log back as a normal user
    page_data['url'] += '1111'
    self.client.post(reverse("pages-edit:update"), page_data)
    self.assertEqual(response.status_code, 403)
    page.delete()

  def test_display_page_menu(self):
    self.superuser_login()  # only superuser can create pages
    page_list_data = [
      {
        'url': '/publish/1rst-title/',
        'title': 'first title',
        'content': 'first content',
      },
      {
        'url': '/publish/level/2nd-title/',
        'title': '2nd title',
        'content': '2nd content',
      },
      {
        'url': '/publish/level/3rd-title/',
        'title': '3rd title',
        'content': '3rd content',
      }
    ]
    pages = [self._test_create_page(page_data) for page_data in page_list_data]
    response = self.client.get(reverse('pages-edit:list'), follow=True)
    self.assertEqual(response.status_code, 200)
    page_icon = icon('page')
    self.assertContains(response, f'''
<a class="navbar-item" href="{flatpage_url(pages[0].url)}">
  {page_icon}
  {pages[0].title}
</a>''', html=True)
    self.assertContains(response, f'''
<div class="navbar-item has-dropdown is-hoverable">
  <p class="navbar-link">{page_icon} level</p>
  <div class="navbar-dropdown is-right">
    <a class="navbar-item" href="{flatpage_url(pages[1].url)}">
      {page_icon} {pages[1].title}
    </a>
    <a class="navbar-item" href="{flatpage_url(pages[2].url)}">
      {page_icon} {pages[2].title}
    </a>
  </div>
</div>''', html=True)

  def test_display_bad_page_menu(self):
    self.superuser_login()  # only superuser can create pages
    bad_page_data = {
        'url': '/foo/1rst-title/',  # doesn't start with /publish=>won't appear in the navbar
        'title': 'first title',
        'content': 'first content',
      }

    bad_page = self._test_create_page(bad_page_data)
    response = self.client.get(reverse('pages-edit:list'), follow=True)
    # print("response", response)
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(response, f'''
<a class="navbar-item" href="{bad_page.url}">
  {icon('page')}
  {bad_page.title}
</a>''', html=True)
