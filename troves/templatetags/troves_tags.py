from django import template

from troves.models import Trove

register = template.Library()


@register.filter(is_safe=True)
def translate_category(category):
    """translate a category"""
    return Trove.translate_category(category)
