from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.filter(is_safe=True)
def members_header(title):
  """generate an html header including a title and an import of Bulma through CDN"""
  return f"""
  <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_(title)}</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bulma@0.9.3/css/bulma.min.css">
  </head>
"""


@register.filter
def birthday_color(when):
  if when == 0:
    return "danger"
  elif when == 1:
    return "warning"
  else:
    return "link"
