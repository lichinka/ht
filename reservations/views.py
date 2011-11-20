import locale
from datetime import date, datetime, timedelta

from django.db import transaction
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from clubs.models import CourtSetup, Court, Vacancy
from ht_utils.views import success
from ht_utils.profile import profile
from accounts.models import UserProfile, ClubProfile
from locations.models import City
from reservations.forms import SearchFreeCourtForm, ReservationForm
from reservations.forms import SelectDateForm, TransferOrDeleteForm
from reservations.models import Reservation
from django.core.exceptions import ObjectDoesNotExist

    
    
@login_required
@transaction.commit_on_success
def transfer_or_delete (request, cs_id, c_id=None):
    """
    Display a form to allow the club decide what to do with
    reservations attached to the received court or court_setup.-
    """
    cs = get_object_or_404 (CourtSetup, pk=cs_id)
    club = UserProfile.objects.get_profile (request.user.username)
    if (club.is_club ( )) and (cs.club == club):
        if request.method == 'POST':
            form = TransferOrDeleteForm (request.POST)
        else:
            form = TransferOrDeleteForm ( )
        #
        # the court setups to where transfer the reservations
        #
        form.fields['transfer_to'].queryset = CourtSetup.objects.filter (club=club) \
                                                                .exclude (id=cs.id)
        #
        # the reservations that may be transfered or deleted
        #
        res_list = Reservation.objects.by_court_setup (cs).order_by ('for_date', 
                                                                     'vacancy__available_from',
                                                                     'vacancy__court__number') \
                                                          .values ('id')
        res_list = [Reservation.objects.get (pk=r['id']) for r in res_list]
                                                                
        if form.is_valid ( ):
            #
            # to transfer reservations means copying and then deleting
            #
            if form.cleaned_data['user_choice'] == 1:
                copied_res = Reservation.objects.copy_to_court_setup (form.cleaned_data['transfer_to'],
                                                                      res_list, 
                                                                      commit=False)
        
        return render_to_response ('reservations/transfer_or_delete.html',
                                   {'form': form,
                                    'res_list': res_list},
                                   context_instance=RequestContext(request))
    else:
        raise Http404


   
@login_required
def cancel (request, r_id):
    """
    Cancels (or deletes) a given reservation, owned by the
    user currently logged in.-
    """
    r = get_object_or_404 (Reservation, pk=r_id)
    if request.user == r.user:
        Reservation.objects.delete (r)
        #
        # redirect to the correct view, based on the user's profile
        #
        if UserProfile.objects.get_profile (request.user.username).is_player ( ):
            return redirect ('ht.views.home')
        elif UserProfile.objects.get_profile (request.user.username).is_club ( ):
            return redirect ('reservations.views.club_view') 
    else:
        #
        # TODO voting for banning a user goes here
        #
        if UserProfile.objects.get_profile (request.user.username).is_club ( ):
            Reservation.objects.delete (r)
            return redirect ('reservations.views.club_view') 
    
    
@login_required
def player_edit (request, v_id, ordinal_date):
    """
    Displays a form to create/edit a reservation for the
    given date (ordinal_date) and vacancy (v_id).
    The user must be a player and the owner of the reservation
    (if it already exists).-
    """
    if UserProfile.objects.get_profile (request.user.username).is_player ( ):
        v = get_object_or_404 (Vacancy, pk=v_id)
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
                             type='P',
                             user=request.user,
                             vacancy=v)
        #
        # the logged-in user should own this reservation
        #
        if request.user == r.user:
            if request.method == 'POST':
                form = ReservationForm (request.POST,
                                        instance=r)
            else:
                form = ReservationForm (initial={'repeat': False,
                                                 'repeat_until': for_date},
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
                                body=_('Your reservation has been processed! \
                                        Please check your message box for possible cancellation \
                                        due to bad weather or other unexpected events.'))
            return render_to_response ('reservations/player_edit.html',
                                       {'form': form,
                                        'ordinal_date': ordinal_date},
                                       context_instance=RequestContext(request))
        else:
            raise Http404
    else:
        raise Http404
    
    
    
@login_required
def club_edit (request, vid, ordinal_date):
    """
    Displays a form to create/edit a reservation for the
    given date (ordinal_date) and vacancy (vid).
    The user must be a club and own the court where the
    reservation is being made.-
    """
    v = get_object_or_404 (Vacancy, pk=vid)
    club = UserProfile.objects.get_profile (request.user.username)
    if (club.is_club ( )) and (v.court.court_setup.club == club):
        for_date = date.fromordinal (int (ordinal_date))
        try:
            r = Reservation.objects.by_date (v.court.court_setup, for_date) \
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
        if request.method == 'POST':
            form = ReservationForm (request.POST,
                                    instance=r)
        else:
            form = ReservationForm (initial={'repeat': False,
                                             'repeat_until': for_date},
                                    instance=r)
        if form.is_valid ( ):
            r = form.save (commit=False)
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
        else:
            #
            # fail silently in case of an invalid date
            #
            for_date = form.fields['for_date'].initial
        #
        # generate a list with all dates of the week containing 'for_date'
        #
        week_date_list = list ( )
        for dow in range (1, 8):
            week_date_list.append (for_date + timedelta (days=dow - for_date.isoweekday ( )))
        #
        # shortcut dates for today, last and next week
        #
        today_date = date.strftime (date.today ( ),
                                   locale.nl_langinfo (locale.D_FMT))
        today_date = today_date.replace (' ', '')
        prev_date = week_date_list[0] - timedelta (days=1)
        prev_date = date.strftime (prev_date, 
                                   locale.nl_langinfo (locale.D_FMT))
        prev_date = prev_date.replace (' ', '')
        next_date = week_date_list[-1] + timedelta (days=1)
        next_date = date.strftime (next_date,
                                   locale.nl_langinfo (locale.D_FMT))
        next_date = next_date.replace (' ', '')
        #
        # court setup
        # 
        cs = CourtSetup.objects.get_active (club)
        #
        # up-to-here we've generated data for the upper part
        # of the page; the table containing the reservations
        # if transfered via AJAX
        #
        if request.is_ajax ( ):
            #
            # hour list
            # 
            hour_list = Vacancy.HOURS[:-1]
            #
            # create the matrix containing the terms that will be displayed
            #
            terms = dict ( )
            avail_courts = Court.objects.get_available (cs).values ('id')
            for d in week_date_list:
                terms[d] = dict ( )
                booked_terms = Reservation.objects.by_date (cs, d) \
                                                  .filter (vacancy__court__id__in=avail_courts) \
                                                  .values ('vacancy__id')
                booked_terms = [e['vacancy__id'] for e in booked_terms]
                v_per_hour_and_court = Vacancy.objects.filter (day_of_week=d.isoweekday ( )) \
                                                      .filter (court__id__in=avail_courts)
                for v in v_per_hour_and_court.iterator ( ):
                    h = v.available_from
                    c_id = v.court.id
                    if h not in terms[d].keys ( ):
                        terms[d][h] = dict ( )
                    if c_id not in terms[d][h].keys ( ):
                        terms[d][h][c_id] = dict ( )
                    terms[d][h][c_id]['vacancy'] = v
                    if v.id in booked_terms:
                        terms[d][h][c_id]['reservation'] = Reservation.objects.by_date (cs, d) \
                                                                              .get (vacancy__id=v.id)
                    else:
                        terms[d][h][c_id]['reservation'] = None
            #
            # finally render the table containing reservations for the week
            #            
            return render_to_response ('reservations/club_view_table.html',
                                       {'week_date_list': week_date_list,
                                        'court_setup': cs,
                                        'hour_list': hour_list,
                                        'terms': terms},
                                       context_instance=RequestContext(request))
        else:
            #
            # render the header part of the page
            #
            return render_to_response ('reservations/club_view.html',
                                       {'form': form,
                                        'court_setup': cs,
                                        'today_date': today_date,
                                        'prev_date': prev_date,
                                        'next_date': next_date},
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
