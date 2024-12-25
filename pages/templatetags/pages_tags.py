import logging
from django.template import Library
from django.conf import settings
from django.utils.safestring import mark_safe

from ..models import FlatPage

register = Library()
logger = logging.getLogger(__name__)


def build_pages_tree(include_predefined=False, prefix=None):
  """
  Based on given flat pages list filters by:
   * "url starting with prefix" if prefix provided, creates a nested tree structure
   * include_predefined flag to filter or not predefined pages
  based on their URLs.

  Returns:
    dict: A dictionary containing the nested tree structure of the flat pages. The dictionary leaves are
    the urls of the flat pages.
  """
  filter = {}
  if not include_predefined:
    filter['predefined'] = False
  if prefix:
    filter['url__istartswith'] = prefix
  # print('filter:', filter)
  pages = FlatPage.objects.filter(**filter) if filter else FlatPage.objects.all()

  page_tree = {}
  last_tree = None
  start = len(prefix) if prefix else 0
  for page in pages:
    trc = ''
    url = page.url[start:-1]
    logger.debug(trc, 'url:', url)
    tree_level = page_tree
    for level in url.split('/'):
      trc += '\t'
      if level == '':
        continue
      logger.debug(trc, 'level:', level)
      if level not in tree_level:
        logger.debug(trc, 'is not in tree_level')
        last_tree = tree_level
        tree_level[level] = {}
      tree_level = tree_level[level]
      logger.debug(trc, "tree for level:", level, "is", last_tree, '\n', trc, 'full tree', page_tree)
    del last_tree[level]
    last_tree[page.title] = page

    logger.debug('tree for url:', page.url, 'is', page_tree)
  logger.debug("final tree:", page_tree)
  return page_tree


@register.inclusion_tag("pages/menu_pages.html")
def pages_menu():
  """
  Creates a nested tree structure from all flat pages that start with the menu page URL prefix
  and pass it to the "pages/menu_pages.html" template for rendering.
  """
  return {'page_tree': build_pages_tree()}


@register.inclusion_tag("pages/page_subtree.html")
def pages_tree(is_superuser=False):
  """
  Creates a nested tree structure from all flat pages and pass it to
  the "pages/page_tree.html" template for rendering.
  """
  # with temporary_log_level(logger, logging.WARNING):
  return {'page_tree': build_pages_tree(include_predefined=is_superuser), 'superuser': is_superuser}


@register.filter
def make_dict(key, value):
  """used in recursive calls of page_subtree.html to transform tuples
    (key, value) returned by dict.items into {key: value} as page_subtree
    can onky deal with dicts.
  """
  return {key: value}


@register.simple_tag
def include_page(url):
  """
  Renders a page based on the provided URL.
  Retrieves the FlatPage object corresponding to the URL and returns its content marked safe
  if found, else raises an error indicating the page was not found in the database.
  Args:
    url (str): The URL of the page to include.

  Returns:
    html: a safe html piece with the content of the page

  Raises:
    Http404: if the page was not found in the database
  """
  # don't use get_object_or_404 here otherwise, there is no mean to get out of the trap
  page = FlatPage.objects.filter(url=url).first()
  if page is None:
    pages = FlatPage.objects.filter(url__iexact=url)
    count = pages.count()
    match count:
      case 0:
        # page not found for the current language, try the default language (ie en-US)
        new_url = url.replace(f'/{settings.LANGUAGE_CODE}/', '/en-US/')
        if new_url != url:
          return include_page(new_url)
        else:
          raise Exception(f'page not found for url={url}')
      case 1:
        page = pages.first()
        logger.info(f'searched for page with url={url}, found {page.url}')
      case _:
        page = pages.first()
        matches = ", ".join([p.url for p in pages])
        logger.warn(f'searched for page with url={url}, found {count} almost matching pages: {matches}, using {page.url}')
  return mark_safe(page.content)


@register.inclusion_tag("pages/link_pages_starting_with.html")
def link_pages_starting_with(url_prefix, icon):
  # don't use get_object_or_404 here otherwise, there is no mean to get out of the trap
  pages = FlatPage.objects.filter(url__istartswith=url_prefix)
  return {'pages': pages, 'icon': icon}
