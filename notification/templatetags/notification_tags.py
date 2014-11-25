from django import template

from notification.models import Notice

register = template.Library ( )



@register.inclusion_tag ('notification/tags/link_to_notices_inbox.html')
def link_to_notices_inbox (usr):
    """
    Renders the number of unseen notices, including
    a link to the 'inbox' containing them.-
    """
    return {'unseen_count': Notice.objects.unseen_count_for (request.user, on_site=True),}

