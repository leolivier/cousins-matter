from django.urls import reverse
from members.tests.tests_member_base import MemberTestCase
from .test_base import BasePageTestCase, TestPageMixin


class TestDisplayPageMenu(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_display_page_menu(self):
    page_list_data = [
      {
        'url': f'{self.pages_prefix}publish/1rst-title/',
        'title': 'first title',
        'content': 'first content',
      },
      {
        'url': f'{self.pages_prefix}publish/level/2nd-title/',
        'title': '2nd title',
        'content': '2nd content',
      },
      {
        'url': f'{self.pages_prefix}publish/level/3rd-title/',
        'title': '3rd title',
        'content': '3rd content',
      }
    ]
    pages = [self._test_create_page(page_data) for page_data in page_list_data]
    response = self.client.get(reverse('pages-edit:list'), follow=True)
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, f'''
<a class="navbar-item" href="{pages[0].url}">
  <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
  {pages[0].title}
</a>''', html=True)
    self.assertContains(response, f'''
<div class="navbar-item has-dropdown is-hoverable">
  <p class="navbar-link">
    <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next"></i></span>
    level
  </p>
  <div class="navbar-dropdown is-right">
    <a class="navbar-item" href="{pages[1].url}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
      {pages[1].title}
    </a>
    <a class="navbar-item" href="{pages[2].url}">
      <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
      {pages[2].title}
    </a>
  </div>
</div>''', html=True)

  def test_display_bad_page_menu(self):
    bad_page_data = {
        'url': f'{self.pages_prefix}1rst-title/',  # doesn't start with /pages/publish=>won't appear in the navbar
        'title': 'first title',
        'content': 'first content',
      }

    bad_page = self._test_create_page(bad_page_data)
    response = self.client.get(reverse('pages-edit:list'), follow=True)
    # print("response", response)
    self.assertEqual(response.status_code, 200)
    self.assertNotContains(response, f'''
<a class="navbar-item" href="{bad_page.url}">
  <span class="icon is-large"><i class="mdi mdi-24px mdi-page-next-outline"></i></span>
  {bad_page.title}
</a>''', html=True)
