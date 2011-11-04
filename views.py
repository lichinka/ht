from django.shortcuts import render_to_response
from django.template.context import RequestContext

from accounts.models import UserProfile



def home (request, template_name='welcome.html'):
    """
    Displays the homepage of this site, depending on the user.-
    """
    if request.user.is_authenticated ( ):
        user = UserProfile.objects.get_profile (request.user.username)
        if user.is_player ( ):
            template_name = 'players/home.html'
        elif user.is_club ( ):
            template_name = 'clubs/home.html'
        
    return render_to_response (template_name,
                               context_instance=RequestContext(request))
