import random
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from cm_main.templatetags.cm_tags import icon

from members.tests.tests_member_base import MemberTestCase
from .test_base import BasePageTestCase, TestPageMixin


class TestDisplayTreePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def create_pages(self):
    page_data = {
        'levels': ['about',
                   settings.MENU_PAGE_URL_PREFIX.replace('/', ''),
                   settings.ADMIN_MESSAGE_PAGE_URL_PREFIX.replace('/', ''),
                   settings.PRIVATE_PAGE_URL_PREFIX.replace('/', '')],
        'title': 'a title',
        'content': 'a content',
      }

    pages = []
    for i in range(5):
      nbl = random.randint(1, 3)
      title = f'{page_data["title"]} #{i+1}'
      slug = slugify(title)
      kind = random.choice(page_data['levels'])
      levels = [kind] + [f'level-{i}' for i in random.sample(range(1, 4), nbl-1)]
      jlevels = '/'.join(levels)
      data = {
        'url': f'/{jlevels}/{slug}/',
        'kind': kind,
        'title': title,
        'content': f'{page_data["content"]} #{i+1}',
        'save': 'true',
      }
      page = self._test_create_page(data)
      pages.append(page)
      # print(data['url'], 'vs', page.url)
    return pages

  def check_pages(self, response, pages, edit=False):
    page_icon = icon('page')
    level_icon = icon('page-level')
    for page in pages:
      if page.url.startswith(settings.MENU_PAGE_URL_PREFIX) or page.url.startswith(settings.PRIVATE_PAGE_URL_PREFIX):
        url = reverse('pages-edit:update', kwargs={'pk': page.id}) if edit else f'/{settings.PAGES_URL_PREFIX}{page.url}'

        self.assertContains(response, f'''
<li class="tree-item">
  {page_icon}
  <span class="tag is-success is-light">
    <a href="{url}">
      {page.title}
    </a>
  </span>
</li>''', html=True)
        levels = list(filter(lambda x: x is not None and x != '', page.url.split('/')))
        nbl = len(levels)
        for idx, level in enumerate(levels):
          if idx == nbl - 1:
            break
          if level == settings.MENU_PAGE_URL_PREFIX.replace('/', ''):
            level = _('Public')
          elif level == settings.PRIVATE_PAGE_URL_PREFIX.replace('/', ''):
            level = _('Private')
          self.assertContains(response, f'''
<span class="tree-level">
  {level_icon}
  <span class="tag is-primary is-light">{level}</span>
</span>''', html=True)
      else:
        self.assertNotContains(response, page.title)

  def test_display_tree_of_pages(self):
    self.client.login(username=self.superuser.username, password=self.superuser.password)  # only superuser can create pages
    pages = self.create_pages()
    response = self.client.get(reverse('pages-edit:tree'), follow=True)
    self.assertEqual(response.status_code, 200)
    self.check_pages(response, pages, edit=True)

    self.client.login(username=self.member.username, password=self.member.password)  # relog as simple user to check tree
    response = self.client.get(reverse('pages-edit:tree'), follow=True)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    self.check_pages(response, pages)

    for page in pages:
      page.delete()
