from django import template

from accounts.models import UserProfile

register = template.Library ( )



@register.inclusion_tag('accounts/user_menu.html')
def user_menu (usr):
    """
    Renders the main menu based on the user type
    and authentication state.-
    """
    profile = UserProfile.objects.get_profile (usr.username) if usr.is_authenticated ( ) else None
    return {'user': usr,
            'profile': profile}


@register.inclusion_tag('accounts/player_information.html')
def player_information (usr):
    """
    Renders some basic personal data belonging to player 'usr'.-
    """
    player = UserProfile.objects.get_profile (usr.username)
    return {'player': player}


@register.inclusion_tag('accounts/club_information.html')
def club_information (usr):
    """
    Renders institutional data belonging to club 'usr'.-
    """
    club = UserProfile.objects.get_profile (usr.username)
    return {'club': club}
