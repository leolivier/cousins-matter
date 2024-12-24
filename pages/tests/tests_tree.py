import random
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

from cm_main.templatetags.cm_tags import icon

from members.tests.tests_member_base import MemberTestCase
from .test_base import BasePageTestCase, TestPageMixin


class TestDisplayTreePage(TestPageMixin, BasePageTestCase, MemberTestCase):
  def test_display_tree_of_pages(self):
    self.superuser_login()  # only superuser can create pages
    page_data = {
        'levels': ['publish', 'level', 'about', 'public', 'private'],
        'title': 'a title',
        'content': 'a content',
      }
    pages = []
    for i in range(5):
      nbl = random.randint(1, 4)
      title = page_data['title']
      title = f'{title} #{i+1}'
      slug = slugify(title)
      levels = []
      for _ in range(nbl):
        levels.append(random.choice(page_data['levels']))
      jlevels = '/'.join(levels)
      title = page_data['title']
      content = page_data['content']
      data = {
        'url': f'/{jlevels}/{slug}/',
        'title': f'{title} #{i+1}',
        'content': f'{content} #{i+1}',
        'save': 'true',
      }
      page = self._test_create_page(data)
      pages.append(page)
      print(data['url'], 'vs', page.url)

    response = self.client.get(reverse('pages-edit:tree'), follow=True)
    self.assertEqual(response.status_code, 200)
    page_icon = icon('page')
    level_icon = icon('page-level')
    for page in pages:
      self.assertContains(response, f'''
<li class="tree-item">
  {page_icon}
  <span class="tag is-success is-light">
    <a href="{reverse('pages-edit:update', kwargs={'pk': page.id})}">
      {page.title}
    </a>
  </span>
</li>''', html=True)
      levels = list(filter(lambda x: x is not None and x != '', page.url.split('/')))
      nbl = len(levels)
      for idx, level in enumerate(levels):
        if idx == nbl - 1:
          break
        self.assertContains(response, f'''
<span class="tree-level">
  {level_icon}
  <span class="tag is-primary is-light">{level}</span>
</span>''', html=True)

    self.login()  # relog as simple user to check tree
    response = self.client.get(reverse('pages-edit:tree'), follow=True)
    # self.print_response(response)
    self.assertEqual(response.status_code, 200)
    page_icon = icon('page')
    level_icon = icon('page-level')
    for page in pages:
      self.assertContains(response, f'''
<li class="tree-item">
  {page_icon}
  <span class="tag is-success is-light">
    <a href="{f'/{settings.PAGES_URL_PREFIX}{page.url}'}">
      {page.title}
    </a>
  </span>
</li>''', html=True)
      levels = list(filter(lambda x: x is not None and x != '', page.url.split('/')))
      nbl = len(levels)
      for idx, level in enumerate(levels):
        if idx == nbl - 1:
          break
        self.assertContains(response, f'''
<span class="tree-level">
  {level_icon}
  <span class="tag is-primary is-light">{level}</span>
</span>''', html=True)

      page.delete()
