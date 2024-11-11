# util functions for member views

from contextlib import contextmanager
import math
from pathlib import PosixPath
from urllib.parse import urlencode

from django.core import paginator
from django.db import connections
from django.forms import ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _


# terrible hack to check if we are in testing mode!!!
IS_TESTING = None


def is_testing():
    global IS_TESTING
    if IS_TESTING is not None:
        return IS_TESTING
    IS_TESTING = False
    for connection in connections.all():
        # print(f"searching test in {connection.settings_dict['NAME']}...")
        if not isinstance(connection.settings_dict['NAME'], PosixPath):
            # print("found")
            IS_TESTING = True
            break
    # print("no test connection found")
    return IS_TESTING


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def redirect_to_referer(request):
    if request.META.get('HTTP_REFERER'):
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect(reverse("cm_main:Home"))


def check_file_size(file, limit):
    if file.size > limit:
        limitmb = math.floor(limit*100/(1024*1024))/100
        sizemb = math.floor(file.size*100/(1024*1024))/100
        filename = file.name
        raise ValidationError(_(f"Uploaded file {filename} is too big ({sizemb}MB), maximum is {limitmb}MB."))


class Paginator(paginator.Paginator):
    possible_per_pages = [10, 25, 50, 100]
    max_pages = 2  # on both sides of the current page link

    def __init__(self, query_set, per_page, reverse_link=None, compute_link=None):
        # example of compute_link=lambda page: reverse('members:members_page', args=[gallery_id, page]))
        if not reverse_link and not callable(compute_link):
            raise TypeError("reverse_link not provided and compute_link is not callable")
        if reverse_link and callable(compute_link):
            raise TypeError("reverse_link provided and compute_link is callable: which one to choose?")
        super().__init__(query_set, per_page)
        self.reverse_link = reverse_link
        self.compute_link = compute_link

    def _get_link(self, idx):
        return self.compute_link(idx) if self.compute_link else reverse(self.reverse_link, args=[idx])

    def get_page_data(self, page_num):
        page_num = min(page_num, self.num_pages)
        page = self.page(page_num)
        # compute a page range from the initial range + or -max-pages
        page.first = max(0, page_num-self.max_pages-1)
        page.last = min(self.num_pages+1, page_num+self.max_pages)
        if page.first == 0:
            page.last = min(self.num_pages+1, 2*self.max_pages+1)
        elif page.last == self.num_pages+1:
            page.first = max(0, page.last-2*self.max_pages-1)
        page.page_range = self.page_range[page.first:page.last]
        page.num_pages = self.num_pages
        # compute page links
        page.page_links = [self._get_link(i) for i in page.page_range]
        page.first_page_link = self._get_link(1)
        page.last_page_link = self._get_link(self.num_pages)
        page.possible_per_pages = self.possible_per_pages
        # pprint(vars(page))
        return page

    @staticmethod
    def get_page(request, object_list, page_num, reverse_link, compute_link=None, default_page_size=100):
      page_size = int(request.GET["page_size"]) if "page_size" in request.GET else default_page_size

      ptor = Paginator(object_list, page_size, reverse_link=reverse_link, compute_link=compute_link)
      page_num = page_num or ptor.num_pages
      if page_num > ptor.num_pages:
          return redirect(ptor._get_link(ptor.num_pages) + '?' + urlencode({'page_size': page_size}))
      return ptor.get_page_data(page_num)


@contextmanager
def temporary_log_level(logger, level):
    original_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(original_level)
