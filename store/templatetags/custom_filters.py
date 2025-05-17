from django import template
from django import forms
import django_filters

register = template.Library()


@register.filter
def is_range_filter(field):
    return isinstance(field.field, django_filters.filters.RangeFilter)

@register.filter
def get_range(value):
    return range(value)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def startswith(value, arg):
    return str(value).startswith(str(arg))

@register.filter
def is_checkbox(widget):
    return isinstance(widget, forms.CheckboxInput)

@register.filter
def is_numberinput(widget):
    return isinstance(widget, forms.NumberInput)

@register.filter(name='div')
def div(value, arg):
    """Безопасное деление для шаблонов"""
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return value / arg
    except (TypeError, ValueError, ZeroDivisionError):
        return 0

@register.filter(name='mul')
def mul(value, arg):
    """Фильтр для умножения значений в шаблоне"""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0