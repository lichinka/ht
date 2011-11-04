from django import template
from django.http import Http404
from django.shortcuts import get_object_or_404

from clubs.models import CourtSetup, Court
from accounts.models import UserProfile


register = template.Library ( )

    
@register.inclusion_tag('clubs/court_properties.html')
def court_properties (court):
    """
    Renders icons for each of the court properties (eg. surface, light, ...)
    """
    try:
        c = get_object_or_404 (Court, pk=court['id'])
    except TypeError:
        #
        # court is the object itself
        #
        c = court
    return {'court' : c,}


@register.inclusion_tag('clubs/court_setup.html')
def court_setup (user):
    """
    Renders a list of court setups for club 'user', indicating
    which one is currently active.-
    """
    club = UserProfile.objects.get_profile (user.username)
    
    if club.is_club ( ):
        return {'court_setup_list' : CourtSetup.objects.filter (club=club).values ( ),}
    else:
        raise Http404
