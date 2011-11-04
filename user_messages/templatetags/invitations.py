from user_messages.models import Message

from django.template import Library



register = Library ( )

@register.inclusion_tag('user_messages/invitations.html')
def display_invitations (user):
    """
    Renders a list of sent and received match invitations
    for the received player 'user'.-
    """
    received_qset = Message.objects.invitations_to (user)
    sent_qset = Message.objects.invitations_from (user)
    return {'received_qset': received_qset,
            'sent_qset': sent_qset}
    