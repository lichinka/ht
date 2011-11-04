from django.http import Http404
from django.contrib import auth
from django.shortcuts import redirect, render_to_response
from django.contrib.auth import views
from django.template.context import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from accounts.models import UserProfile
from accounts.forms import RegisterUserForm, EditPlayerProfileForm



def register (request):
    """
    Displays a form to register a new player.-
    """
    if not request.user.is_authenticated ( ):
        post_data = request.POST if request.method == 'POST' else None
        form = RegisterUserForm (post_data)
        if form.is_valid ( ):
            #
            # use the email address as user name
            #
            new_user = User.objects.create_user (username=form.cleaned_data['email'],
                                                 email=form.cleaned_data['email'],
                                                 password=form.cleaned_data['pass1'])
            new_user = auth.authenticate (username=new_user.username,
                                          password=form.cleaned_data['pass1'])
            if new_user:
                #
                # create a default profile and log the new user in
                #
                pp = UserProfile.objects.create_player_profile (new_user.username)
                auth.login (request, new_user)
                return redirect ('accounts.views.edit_player_profile',
                                 id=pp.id)
        
        return render_to_response ('accounts/register.html',
                                   {'form': form,},
                                   context_instance=RequestContext(request))
    else:
        return redirect (reverse ('ht.views.home'))



@login_required
def edit_player_profile (request):
    """
    Displays a form to edit the player's profile.-
    """
    pp = UserProfile.objects.get_profile (request.user.username)
    if pp.is_player ( ):
        if request.method == 'POST':
            form = EditPlayerProfileForm (request.POST,
                                          instance=pp)
        else:
            form = EditPlayerProfileForm (initial={'user': pp.user,
                                                   'first_name': pp.user.first_name,
                                                   'last_name': pp.user.last_name,},
                                          instance=pp)
        if form.is_valid ( ):
            pp = form.save (commit=False)
            pp.user = request.user
            pp.user.first_name = form.cleaned_data['first_name']
            pp.user.last_name = form.cleaned_data['last_name']
            pp.user.save ( )
            pp.save ( )
            #
            # go to the next page
            #
            if not form.cleaned_data['next']:
                form.cleaned_data['next'] = reverse ('ht.views.home')
            return redirect (form.cleaned_data['next'])
        
        return render_to_response ('accounts/edit_player_profile.html',
                                   {'form': form,},
                                   context_instance=RequestContext(request))
    else:
        raise Http404


            
@login_required
def display_profile (request):
    """
    Display the player's or club's profile page.-
    """
    if UserProfile.objects.get_profile (request.user.username).is_player ( ):
        return render_to_response ("accounts/display_player_profile.html",
                                   context_instance=RequestContext(request))
    if UserProfile.objects.get_profile (request.user.username).is_club ( ):
        return render_to_response ("accounts/display_club_profile.html",
                                   context_instance=RequestContext(request))
    else:
        raise Http404
        
    
    
def login (request):
    """
    Displays the login form or logs a user in.-
    """
    if request.user.is_authenticated ( ):
        return redirect (reverse ('ht.views.home'))
    else:
        return views.login (request, 'accounts/login.html')



def logout (request):
    """
    Logs the user out, redirecting her to the home page.-
    """
    return views.logout (request, next_page=reverse ('ht.views.home'))
