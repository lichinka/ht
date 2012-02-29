from django import template
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext



register = template.Library ( )


@register.inclusion_tag ('ht_utils/text_only.html')
def text_only (text, title=None, next_text=None, next_url=None):
    """
    Renders 'text', which may contain simple HTML, under the given
    'title'. It displays a button with text 'next_text' and target
    'next_url'. This value is then translated using 'reverse'.- 
    """
    if next_url is None:
        next_url = 'home'
    return {'text':      text,
            'title':     title,
            'next_text': next_text,
            'next_url':  next_url,}


@register.inclusion_tag ('ht_utils/vertical_form.html')
def vertical_form (form, action_view, action_text='Save', next_url=None):
    """
    Renders a form with its fields arranged vertically, using the
    given 'form', 'action_view', 'action_text' and 'next_url' where 
    needed.-
    """
    return {'form': form,
            'action_view': action_view,
            'action_text': action_text,
            'next_text': None,
            'next_url': next_url,}


@register.inclusion_tag ('ht_utils/discard_button.html')
def discard_button (next_text=None, next_url=None):
    """
    Renders the discard button with label 'next_text', which will 
    redirect the user to the given URL in 'next_url'. This value is
    then translated using 'reverse'.- 
    """
    if next_text is None:
        next_text = ugettext ('Discard')
    if next_url is None:
        next_url = 'home'
    next_url = reverse (next_url)
    return {'next_text': next_text,
            'next_url': next_url,}
