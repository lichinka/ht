from players.models import Vacancy
from accounts.models import PlayerProfile

from django import template

register = template.Library ( )


@register.inclusion_tag('players/availability.html')
def availability (user, invite=None, delete=None):
    """
    Renders a list of terms for which the received player
    'user' is available for playing.
    The parameters 'invite' and 'delete' indicate the links that
    should be rendered for each vacancy displayed. They may be 
    set to 1 or 0 as required.-
    """
    player = PlayerProfile.objects.filter (user=user)
    if (player):
        player_vacancy = Vacancy.objects.filter (player=player)
    else:
        player_vacancy = Vacancy.objects.none ( )
    return {'vacancy_list': player_vacancy.iterator,
            'invite': invite,
            'delete': delete}
