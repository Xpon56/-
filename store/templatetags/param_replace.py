from django import template

register = template.Library()

@register.simple_tag
def param_replace(request, **kwargs):
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value:
            params[key] = value
        else:
            params.pop(key, None)
    return params.urlencode()