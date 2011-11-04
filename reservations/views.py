from datetime import date, datetime, timedelta

from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from clubs.models import CourtSetup, Court, Vacancy
from ht_utils.views import success
from accounts.models import UserProfile, ClubProfile
from locations.models import City
from reservations.forms import SearchFreeCourtForm, ReservationForm, SelectDateForm
from reservations.models import Reservation
from django.core.exceptions import ObjectDoesNotExist

    
    
@login_required
def player_edit (request, v_id, ordinal_date):
    """
    Displays a form to create/edit a reservation for the
    given date (ordinal_date) and vacancy (v_id).
    The user must be a player.-
    """
    if UserProfile.objects.get_profile (request.user.username).is_player ( ):
        if ordinal_date:
            for_date = date.fromordinal (int (ordinal_date))
        v = get_object_or_404 (Vacancy, pk=v_id)
        r = Reservation.objects.filter (for_date=for_date,
                                        vacancy=v)
        if r:
            #
            # we are editing an existing reservation
            #
            r = r[0]
        else:
            #
            # create a new reservation in-memory
            #
            r = Reservation (created_on=datetime.now ( ),
                             for_date=for_date,
                             user=request.user,
                             vacancy=v)
        post_data = request.POST if request.method == 'POST' else None
        form = ReservationForm (post_data,
                                instance=r)
        if form.is_valid ( ):
            r = form.save (commit=False)
            #
            # save which user made the reservation
            # and the reservation type
            #
            r.user = request.user
            r.type = 'P'
            #
            # add the user's name to the description
            #
            r.description = '%s, %s' % (r.user.last_name,
                                        r.user.first_name)
            r.save ( )
            return success (request,
                            title=_('Reservation sent'),
                            body=_('''Your reservation has been processed!
                                      Please check your message box for possible cancellation due to weather or other unexpected events.'''))
        return render_to_response ('reservations/player_edit.html',
                                   {'form': form,
                                    'ordinal_date': ordinal_date},
                                   context_instance=RequestContext(request))
    else:
        raise Http404
    
    
    
@login_required
def club_edit (request, vid, ordinal_date):
    """
    Displays a form to create/edit a reservation for the
    given date (ordinal_date) and vacancy (vid).
    The user must be a club.-
    """
    v = get_object_or_404 (Vacancy, pk=vid)
    club = UserProfile.objects.get_profile (request.user.username)
    if (club.is_club ( )) and (v.court.court_setup.club == club):
        for_date = date.fromordinal (int (ordinal_date))
        try:
            r = Reservation.objects.filter (for_date=for_date) \
                                   .get (vacancy=v)
        except ObjectDoesNotExist:
            #
            # create a new reservation in-memory
            #
            r = Reservation (created_on=datetime.now ( ),
                             for_date=for_date,
                             type='C',
                             user=request.user,
                             vacancy=v)
            
        post_data = request.POST if request.method == 'POST' else None
        form = ReservationForm (post_data,
                                instance=r)
        if form.is_valid ( ):
            r = form.save (commit=False)
            #
            # save which user made the reservation
            # and the reservation type
            #
            r.user = request.user
            r.type = 'C'
            #
            # add the club's name if no description has been given
            #
            if not r.description.strip ( ):
                r.description = '%s %s' % (r.user.first_name,
                                           r.user.last_name)
            r.save ( )
            return redirect ('reservations.views.club_view')
        return render_to_response ('reservations/club_edit.html',
                                   {'form': form,
                                    'ordinal_date': ordinal_date},
                                   context_instance=RequestContext(request))
    else:
        raise Http404
    
    
    
@login_required
def club_view (request):
    """
    Displays a table containing all active reservations for the
    received date, per hour and per court in the current court setup.-
    """
    club = UserProfile.objects.get_profile (request.user)
    if club.is_club ( ):
        post_data = request.POST if request.method == 'POST' else None
        form = SelectDateForm (post_data)
        if form.is_valid ( ):
            for_date = form.cleaned_data['for_date']
            prev_date = for_date - timedelta (days=1)
            next_date = for_date + timedelta (days=1)
            form = SelectDateForm (initial={'for_date': for_date,
                                            'prev_date': prev_date,
                                            'next_date': next_date,})
        else:
            #
            # fail silently in case of an invalid date
            #
            form = SelectDateForm ( )
        cs = CourtSetup.objects.get_active (club)
        court_list = Court.objects.get_available (cs) \
                                  .order_by ('number')
        hour_list = Vacancy.HOURS[:-1]
        return render_to_response ('reservations/club_view.html',
                                   {'court_list': court_list,
                                    'court_setup': cs,
                                    'form': form,
                                    'hour_list': hour_list},
                                   context_instance=RequestContext(request))
    else:
        raise Http404
    


def search (request, template_name='reservations/search.html'):
    """
    Displays a form to search for a free court, and
    reserve a vacancy term from the displayed results.-
    """
    params = {}
    if request.method == 'POST':
        params['form'] = SearchFreeCourtForm (request.POST)
        if params['form'].is_valid ( ):
            #
            # filter by location
            #
            if params['form'].cleaned_data['location']:
                club_list = ClubProfile.objects.filter (city=params['form'].cleaned_data['location'])
            else:
                club_list = ClubProfile.objects.all ( )
            params['club_list'] = club_list.values ( )
            
            for club in params['club_list']:
                club['name'] = User.objects.get (pk=club['user_id'])
                club['name'] = "%s %s" % (club['name'].first_name,
                                          club['name'].last_name)
                club['city'] = City.objects.get (pk=club['city_id'])
                cs = CourtSetup.objects.get_active (club)
                club['court_list'] = Court.objects.get_available(cs).values ( )
            #
            # filter by date
            #
            params['for_date'] = date.fromordinal (int (params['form'].cleaned_data['for_date']))
            #
            # filter by time
            #
            hour_list = [int(k) for k,v in Vacancy.HOURS]
            selected_time = params['form'].cleaned_data['for_time']
            if selected_time == 'XX':
                selected_time = hour_list.index (14)
            elif selected_time == 'AM':
                selected_time = hour_list.index (7)
            elif selected_time == 'PM':
                selected_time = hour_list.index (13)
            elif selected_time == 'EV':
                selected_time = hour_list.index (18)
            else:
                selected_time = hour_list.index (int(selected_time))
            #
            # display six vacancy terms, including the selected time
            #
            params['hour_list'] = []
            hour_list_len = 6
            # ignore the last term at midnight
            vacancy_hours = Vacancy.HOURS[:-1]
            if (len(vacancy_hours) - selected_time) < hour_list_len:
                #
                # fill with terms earlier than the selected time
                #
                selected_time = len(vacancy_hours) - hour_list_len
            for i in range (selected_time, selected_time + 6):
                params['hour_list'].append (vacancy_hours[i])
            #
            # shortcuts for previous and next day
            #
            min_date = date.fromordinal (int (SearchFreeCourtForm.DATES[0][0]))
            max_date = date.fromordinal (int (SearchFreeCourtForm.DATES[-1][0]))
            
            if params['for_date'] == min_date:
                params['prev_day'] = None
            else:
                params['prev_day'] = params['for_date'] - timedelta (days=1)
                params['prev_day'] = date.strftime (params['prev_day'],
                                                    '%A, %x')
                
            if params['for_date'] == max_date:
                params['next_day'] = None
            else:
                params['next_day'] = params['for_date'] + timedelta (days=1)
                params['next_day'] = date.strftime (params['next_day'],
                                                    '%A, %x')
            #
            # shortcuts for earlier and later times
            #
            earlier = max (selected_time - 3, 0)
            params['earlier'] = vacancy_hours[earlier][0]
            later = min (selected_time + 3, len(vacancy_hours) - 1)
            params['later'] = vacancy_hours[later][0]
            #
            # change the template to display the results
            #
            template_name = 'reservations/user_view.html'
    else:
        params['form'] = SearchFreeCourtForm ( )
        
    return render_to_response (template_name,
                               params,
                               context_instance=RequestContext(request))
