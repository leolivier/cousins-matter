import logging
from django.template import Library
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
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
  start = len(settings.MENU_PAGE_URL_PREFIX)
  for page in menu_pages:
    url = page.url[start:-1]
    logger.debug('url:', url)
    tree_level = page_tree
    for level in url.split('/'):
      if level == '':
        continue
      logger.debug('level:', level)
      if level not in tree_level:
        logger.debug('level not in tree_level')
        tree_level[level] = {}
        last_tree = tree_level
      tree_level = tree_level[level]
      logger.debug("tree for level:", level, "is", page_tree)
    last_tree[level] = page
    logger.debug('tree for url:', page.url, 'is', page_tree)
  logger.debug("final tree:", page_tree)
  return {'page_tree': page_tree}


@register.inclusion_tag("pages/sidemenu_pages.html")
def pages_sidemenu():
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
  start = len(settings.MENU_PAGE_URL_PREFIX)
  for page in menu_pages:
    url = page.url[start:-1]
    logger.debug('url:', url)
    tree_level = page_tree
    for level in url.split('/'):
      if level == '':
        continue
      logger.debug('level:', level)
      if level not in tree_level:
        logger.debug('level not in tree_level')
        tree_level[level] = {}
        last_tree = tree_level
      tree_level = tree_level[level]
      logger.debug("tree for level:", level, "is", page_tree)
    last_tree[level] = page
    logger.debug('tree for url:', page.url, 'is', page_tree)
  logger.debug("final tree:", page_tree)
  return {'page_tree': page_tree}


@register.inclusion_tag("pages/include_page.html")
def include_page(url):
  """
  Renders a page based on the provided URL. 
  Retrieves the FlatPage object corresponding to the URL and returns its content
  if found, else returns a message indicating the page was not found in the database.
  The resulting content is passed to the "pages/include_page.html" template for rendering.
  Args:
    url (str): The URL of the page to include.

  Returns:
    dict: A dictionary containing the content of the page if it exists, 
          or an error message if the page is not found.
  """
  # don't use get_object_or_404 here otherwise, there is no mean to get out of the trap
  page = FlatPage.objects.filter(url=url).first()
  return {'content': page.content if page is not None else _(f"Cannot load page from url {url}, it was not found in the "
                                                             "database. Please contact the administrator of the site")}


@register.inclusion_tag("pages/link_pages_starting_with.html")
def link_pages_starting_with(url_prefix, css_class='', hr=''):
  # don't use get_object_or_404 here otherwise, there is no mean to get out of the trap
  pages = FlatPage.objects.filter(url__istartswith=url_prefix)
  return {'pages': pages, 'css_class': css_class, 'hr': hr}
