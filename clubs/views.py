from django.db import transaction
from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required

import ht_utils
from clubs.forms import EditCourtSetupForm, EditCourtPropertiesForm
from clubs.models import CourtSetup, Court, Vacancy
from accounts.models import UserProfile



@login_required
def clone_court_setup (request, cs_id):
    """
    Clones a court setup of a club, including all its courts, 
    their properties and vacancy terms, and displays it.-
    """
    cs = get_object_or_404 (CourtSetup, pk=cs_id)
    club = UserProfile.objects.get_profile (request.user) 
    if (club.is_club ( )) and (cs.club == club):
        clone = CourtSetup.objects.clone (cs)
        return redirect ('clubs.views.edit_court_setup',
                         cs_id=clone.id)
    else:
        raise Http404
    
    
    
@login_required
def delete_court_setup (request, cs_id):
    """
    Deletes a court setup of a club, prior confirmation.-
    """
    club = UserProfile.objects.get_profile (request.user)
    if club.is_club ( ):
        cs = get_object_or_404 (CourtSetup, pk=cs_id)
        #
        # do not allow the deletion of the last court setup of this club
        #
        if CourtSetup.objects.get_count (club) > 1:
            cs.delete ( )
        return redirect ('accounts.views.display_profile')
    else:
        raise Http404
    
    
    
@login_required
def delete_court (request, c_id):
    """
    Deletes a court within a court setup, including all its 
    properties and vacancy terms.-
    """
    if UserProfile.objects.get_profile (request.user).is_club ( ):
        c = get_object_or_404 (Court, pk=c_id)
        cs = c.court_setup
        #
        # do not allow the deletion of the last court
        #
        if Court.objects.get_count (cs) > 1:
            c.delete ( )
        return redirect ('clubs.views.edit_court_setup',
                         cs_id=cs.id)
    else:
        raise Http404
    
    
    
@login_required
def clone_court (request, c_id):
    """
    Clones a court within a court setup, including all its 
    properties and vacancy terms, and displays it.-
    """
    if UserProfile.objects.get_profile (request.user).is_club ( ):
        c = get_object_or_404 (Court, pk=c_id)
        clone = Court.objects.clone (c)
        return redirect ('clubs.views.edit_court_setup',
                         cs_id=clone.court_setup.id,
                         c_id=clone.id)
    else:
        raise Http404



@login_required
def edit_court_setup (request, cs_id, c_id=None):
    """
    Displays a form to edit the court setup with 'cs_id',
    and court 'c_id'.-
    """
    cs = get_object_or_404 (CourtSetup, pk=cs_id)
    club = UserProfile.objects.get_profile (request.user) 
    if (club.is_club ( )) and (cs.club == club):
        if request.method == 'POST':
            form = EditCourtSetupForm (request.POST, instance=cs)
            if form.is_valid ( ):
                form.save ( )
                return redirect ('accounts.views.display_profile')
        else:
            form = EditCourtSetupForm (instance=cs)
        day_list = Vacancy.DAYS
        hour_list = Vacancy.HOURS[:-1]
        court_list = Court.objects.filter (court_setup=cs) \
                                  .order_by ('number') \
                                  .values ( )
        selected_court = Court.objects.get (pk=c_id) if c_id else court_list[0]
          
        return render_to_response ('clubs/edit_court_setup.html',
                                   {'day_list': day_list,
                                    'hour_list': hour_list,
                                    'form': form,
                                    'court_setup_id': cs_id,
                                    'court_list': court_list,
                                    'selected_court': selected_court},
                                   context_instance=RequestContext(request))
    else:
        raise Http404



@login_required
def save_court_vacancy (request, id):
    """
    Saves the all vacancy terms and prices of court with 'id'.-
    """
    if UserProfile.objects.get_profile (request.user).is_club ( ):
        court = get_object_or_404 (Court, pk=id)
        #
        # prevent users from changing other club's court
        #
        if request.user == court.court_setup.club.user:
            if request.method == 'POST':
                #
                # save the new prices in a container for bulk update
                #
                prices = {}
                v_ids = [(k.split('_')[1], v) for k,v in request.POST.items ( ) if 'price' in k]
                for k,v in v_ids:
                    try:
                        price = '%10.2f' % float (ht_utils.number_to_default_locale (v))
                    except ValueError:
                        price = None
                    if price not in prices.keys ( ):
                        prices[price] = []
                    prices[price].append (k)
                #
                # bulk update all vacancy terms
                #
                for p in prices.keys ( ):
                    Vacancy.objects.filter (id__in=prices[p]).update (price=p)
                    
            return redirect ('clubs.views.edit_court_setup',
                             cs_id=court.court_setup.id,
                             c_id=court.id)
        else:
            raise Http404
    else:
        raise Http404
    
    
    
@login_required
@transaction.commit_on_success
def toggle_active_court_setup (request, cs_id):
    """
    Changes the state of the 'is_active' flag of court setup
    with 'cs_id', and redisplays the club profile page.-
    """
    cs = get_object_or_404 (CourtSetup, pk=cs_id)
    #
    # only club owners are allowed to change their court setup
    #
    club = UserProfile.objects.get_profile (request.user.username)
    if (club.is_club ( )) and (cs.club == club):
        #
        # cannot turn off an active court setup
        #
        if not cs.is_active:
            #
            # deactivate the currently active court setup
            # and activate the new one
            #
            cs_act = CourtSetup.objects.get_active (club)
            cs_act.is_active = False
            cs_act.save ( )
            cs.is_active = True
            cs.save ( )
        return redirect ('accounts.views.display_profile')
    else:
        raise Http404
    
    
    
@login_required
def toggle_available_court (request, c_id):
    """
    Changes the state of the 'is_available' flag of court
    with 'c_id', and redisplays the court setup.-
    """
    c = get_object_or_404 (Court, pk=c_id)
    c.is_available = not c.is_available
    c.save ( )
    return redirect ('clubs.views.edit_court_setup',
                     cs_id=c.court_setup.id,
                     c_id=c_id)
   
    
    
@login_required
def edit_court_properties (request, cs_id, c_id):
    """
    Displays a form to edit the properties (e.g. surface, light, ...)
    of court with 'c_id', belonging to court setup with 'cs_id'.-
    """
    if UserProfile.objects.get_profile (request.user).is_club ( ):
        court = get_object_or_404 (Court, pk=c_id)
        post_data = request.POST if request.method == 'POST' else None
        form = EditCourtPropertiesForm (post_data,
                                        instance=court)
        if form.is_valid ( ):
            court.save ( )
            return redirect ('clubs.views.edit_court_setup',
                             cs_id=court.court_setup.id,
                             c_id=court.id)
            
        return render_to_response ('clubs/edit_court_properties.html',
                                   {'form': form,
                                    'court': court,
                                    'court_setup_id': cs_id},
                                   context_instance=RequestContext(request))
    else:
        raise Http404
