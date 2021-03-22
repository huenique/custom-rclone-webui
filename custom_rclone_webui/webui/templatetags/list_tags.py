from django import template

register = template.Library()


@register.filter
def next(some_list, current_index):
    """
    Returns the next element of the list using the current index if it exists.
    Otherwise returns an empty string.

    https://docs.djangoproject.com/en/3.0/howto/custom-template-tags/#writing-custom-template-filters
    """
    try:
        return some_list[int(current_index) + 1]
    except:
        pass
