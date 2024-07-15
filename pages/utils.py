from django.conf import settings
from django.urls import reverse
from django.contrib.flatpages.views import flatpage


def flatpage_url(relative_url):
  url = reverse(flatpage, None, [relative_url]).replace(f'{settings.PAGES_URL_PREFIX}/', f'{settings.PAGES_URL_PREFIX}')
  # print(url)
  return url
