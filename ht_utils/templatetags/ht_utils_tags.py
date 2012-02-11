from django import template
from django.core.urlresolvers import reverse



register = template.Library ( )


@register.inclusion_tag('ht_utils/discard_button.html')
def discard_button (next_url=None):
    """
    Renders the discard button, which will redirect the user
    to the given URL in 'next'.-
    """
    if next_url is None:
        next_url = reverse ('home')
    return {'next_url': next_url,}
