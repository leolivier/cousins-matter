from django.template import Library, Node, Variable, TemplateSyntaxError
from django.conf import settings
from django.urls import reverse, resolve, NoReverseMatch
from django.utils.translation import gettext as _

register = Library()

@register.simple_tag
def title(title_s):
    return f"{settings.SITE_NAME} - {_(title_s)}"