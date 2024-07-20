import logging
from django.http import Http404
from django.template import Library
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

register = Library()
logger = logging.getLogger(__name__)


@register.inclusion_tag("pages/menu_pages.html")
def pages_menu():
  """
  Retrieves all flat pages that start with the menu page URL prefix and creates a nested tree structure
  based on their URLs. The resulting tree is passed to the "pages/menu_pages.html" template for rendering.

  Returns:
    dict: A dictionary containing the nested tree structure of the flat pages. The dictionary leaves are
    the urls of the flat pages.
  """
  menu_pages = FlatPage.objects.filter(url__istartswith=settings.MENU_PAGE_URL_PREFIX)
  # logger.debug(menu_pages.query)
  page_tree = {}
  last_tree = None
  start = len(settings.MENU_PAGE_URL_PREFIX)
  for page in menu_pages:
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
  return {'page_tree': page_tree}


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
    raise Http404(_(f"Cannot load page from url {url}, it was not found in the "
                    "database. Please contact the administrator of the site"))
  return mark_safe(page.content)


@register.inclusion_tag("pages/link_pages_starting_with.html")
def link_pages_starting_with(url_prefix, icon):
  # don't use get_object_or_404 here otherwise, there is no mean to get out of the trap
  pages = FlatPage.objects.filter(url__istartswith=url_prefix)
  return {'pages': pages, 'icon': icon}
