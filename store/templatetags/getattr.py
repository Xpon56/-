from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    return obj.get(attr, [])

@register.filter
def getlist(obj, attr):
    return obj.getlist(attr)