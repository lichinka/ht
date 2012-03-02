import urlparse

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect, render_to_response
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.contrib.auth import views
from django.template.context import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.sites.models import get_current_site
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

from actstream import action
from ht_utils.views import get_next_url
from accounts.forms import (EditPlayerProfileForm, EditClubProfileForm,
                            EditUserLoginData)
from accounts.models import UserProfile



@login_required
def change_password (request,
                     template_name='accounts/change_password.html',
                     post_change_redirect=None,
                     password_change_form=PasswordChangeForm):
    """
    Displays a page to change the password.-
    """
    if post_change_redirect is None:
        post_change_redirect = reverse ('accounts_change_password_done')
    if request.method == "POST":
        form = password_change_form (user=request.user, data=request.POST)
        if form.is_valid ( ):
            form.save ( )
            return HttpResponseRedirect (post_change_redirect)
    else:
        form = password_change_form (user=request.user)
    return render_to_response (template_name,
                               {'form': form,},
                               context_instance=RequestContext (request))


@login_required
def change_password_done (request,
                          template_name='accounts/change_password_done.html'):
    """
    Displays a static page informing the user about the password change.
    It also registers this action in the user's log.-
    """
    action.send (request.user, verb='changed password')
    return render_to_response (template_name,
                               context_instance=RequestContext (request))
   
    
@login_required
def edit_user_login_data (request,
                          template_name='accounts/edit_user_login_data.html'):
    """
    Displays a form to edit a user's email address.-
    """
    next_url = get_next_url (request,
                             'accounts_display_profile')
    post_data = request.POST if request.method == 'POST' else None
    form = EditUserLoginData (post_data, 
                              instance=request.user)
    if form.is_valid ( ):
        form.save ( )
        #
        # go back to where 'next_url' points
        #
        return redirect (next_url)
    return render_to_response (template_name,
                               {'form': form,
                                'next_url': next_url},
                               context_instance=RequestContext(request))


@login_required
def edit_club_profile (request,
                       template_name='accounts/edit_club_profile.html'):
    """
    Displays a form to edit a club's profile.-
    """
    cp = UserProfile.objects.get_profile (request.user.username)
    if cp.is_club ( ):
        next_url = get_next_url (request,
                                 'accounts_display_profile')
        post_data = request.POST if request.method == 'POST' else None
        form = EditClubProfileForm (post_data,
                                    instance=cp)
        if form.is_valid ( ):
            cp = form.save (commit=False)
            cp.user = request.user
            cp.save ( )
            #
            # go back to where 'next_url' points
            #
            return redirect (next_url)
        return render_to_response (template_name,
                                   {'form': form,
                                    'next_url': next_url},
                                   context_instance=RequestContext(request))
    else:
        raise Http404


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
            # go back to the profile page
            return redirect (reverse ('accounts_display_profile'))

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


@csrf_protect
@never_cache
def login (request, template_name='accounts/login.html',
           redirect_field_name=REDIRECT_FIELD_NAME,
           authentication_form=AuthenticationForm,
           current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    Code from 'django.contrib.auth.views.login'.-
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            netloc = urlparse.urlparse(redirect_to)[1]

            # Use default setting if redirect_to is empty
            if not redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Security check -- don't allow redirection
            # to a different host.
            elif netloc and netloc != request.get_host():
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            # Save the action of the user logging in
            action.send (form.get_user ( ),
                         verb='logged in')

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    context.update(extra_context or {})
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request, current_app=current_app))


def logout (request):
    """
    Logs the user out, redirecting her to the home page.-
    """
    if request.user.is_authenticated ( ):
        action.send (request.user, verb='logged out')
    return views.logout (request, next_page=reverse ('ht.views.home'))

