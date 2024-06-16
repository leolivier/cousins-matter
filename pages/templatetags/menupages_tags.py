from django.shortcuts import get_object_or_404
from django.template import Library
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError

register = Library()

menu_pages_url_prefix = f'/{settings.PAGES_URL_PREFIX}/publish/'


def loop_on_menupages(menu_pages, page_tree, level):
  done = True
  for page in menu_pages:
    tree_level = page_tree
    upper_tree = None
    item = page.split_url[level] if level < len(page.split_url) else None
    for upper_level in page.split_url[0:level]:
      if not upper_level:
        break
      if upper_level in tree_level:
        upper_tree = tree_level
        tree_level = tree_level[upper_level]
      else:
        raise ValueError("cant find %s" % upper_level)  # should have been put by previous level
    if item:
      if isinstance(tree_level, FlatPage):
        raise ValidationError(_("A flatpage cannot be a subpage of another flatpage, check your URLs"))
      done = False
      if item not in tree_level:
        tree_level[item] = {}
    elif upper_level:
      if not page.url.startswith(menu_pages_url_prefix):
        page.url = menu_pages_url_prefix + page.url
      upper_tree[upper_level] = page
  return done


@register.inclusion_tag("pages/menu_pages.html")
def get_menu_pages():
  menu_pages = FlatPage.objects.filter(url__startswith=menu_pages_url_prefix)

  for page in menu_pages:
    page.url = page.url[len(menu_pages_url_prefix):]
    page.split_url = page.url.split('/')

  page_tree = {page.split_url[0]: {} for page in menu_pages}
  done = False
  level = 1
  while not done:
    done = loop_on_menupages(menu_pages, page_tree, level)
    level += 1
  # print("tree:", page_tree)
  return {'page_tree': page_tree}


@register.inclusion_tag("pages/menu_pages_level.html")
def menu_level(level, sublevels):
  return {'level': level, 'sublevels': sublevels}


@register.inclusion_tag("pages/include_page.html")
def include_page(url):
  # print("including page", url)
  page = get_object_or_404(FlatPage, url=url)
  return {'content': page.content}
