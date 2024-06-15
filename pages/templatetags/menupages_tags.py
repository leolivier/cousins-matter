from django.template import Library
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
from django.utils.translation import gettext as _

register = Library()


@register.inclusion_tag("pages/menu_pages.html")
def get_menu_pages():
  menu_pages_url_prefix = f'/{settings.PAGES_URL_PREFIX}/publish/'
  menu_pages = FlatPage.objects.filter(url__startswith=menu_pages_url_prefix)

  for page in menu_pages:
    page.url = page.url[len(menu_pages_url_prefix):]
    page.split_url = page.url.split('/')

  page_tree = {page.split_url[0]: {} for page in menu_pages}
  done = False
  level = 1
  while not done:
    # print("==========================\nlevel:", level, "tree:", page_tree)
    done = True
    for page in menu_pages:
      tree_level = page_tree
      upper_tree = None
      item = page.split_url[level] if level < len(page.split_url) else None
      # print("url:", page.url, "item:", item)
      for upper_level in page.split_url[0:level]:
        if not upper_level:
          break
        # print("upper level:", upper_level, "tree_level:", tree_level)
        if upper_level in tree_level:
          upper_tree = tree_level
          tree_level = tree_level[upper_level]
        else:
          raise ValueError("cant find %s" % upper_level)  # should have been by previous level
      # print('tree level selected inside', upper_tree)
      if item:
        if isinstance(tree_level, FlatPage):
          raise ValueError(_("A page cannot be a subpage of another page, check your URLs"))
        done = False
        if item not in tree_level:
          tree_level[item] = {}
          # print("added item to tree level:", tree_level)
      elif upper_level:
        # print("at end, adding page", page.title)
        if not page.url.startswith(menu_pages_url_prefix):
          page.url = menu_pages_url_prefix + page.url
        upper_tree[upper_level] = page
      # print("upper tree:", upper_tree)
    level += 1

  # print("tree:", page_tree)
  return {'page_tree': page_tree}


@register.inclusion_tag("pages/menu_pages_level.html")
def menu_level(level, sublevels):
  return {'level': level, 'sublevels': sublevels}