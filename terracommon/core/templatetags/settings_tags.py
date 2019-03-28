from django import template
from django.conf import settings
from django.utils.html import mark_safe

register = template.Library()


@register.simple_tag
def front_url():
    return mark_safe(settings.FRONT_URL)


@register.simple_tag
def hostname():
    return mark_safe(settings.HOSTNAME)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
