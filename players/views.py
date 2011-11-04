import random

from django.http import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

import user_messages
from accounts.models import PlayerProfile, UserProfile
from players.models import Vacancy
from players.forms import EditVacancyForm, SearchOpponentForm



@login_required
def edit_vacancy (request):
    """
    Changes a player's availability for play.-
    """
    player = UserProfile.objects.get_profile (request.user.username)
    
    if player.is_player ( ):
        player_profile = request.user.get_profile ( ).player_profile
        player_vacancy = Vacancy.objects.filter (player=player)
        
        if request.method == 'POST':
            form = EditVacancyForm (request.POST)
        else:
            v = Vacancy ( )
            v.player = player_profile
            form = EditVacancyForm (instance=v)
           
        return render_to_response ('players/vacancy.html',
                                   {'form': form,
                                    'player_vacancy': player_vacancy},
                                   context_instance=RequestContext(request))
    else:
        raise Http404
    
    
    
@login_required
def add_vacancy (request):
    """
    Adds a player's time and place for play.-
    """
    #
    # Create a new form with the received data ...
    #
    form = EditVacancyForm (request.POST or None)
    #
    # ... add the data about the logged-in user ...
    #
    form.instance.player = request.user.get_profile ( ).player_profile
    #
    # ... find out if everything is valid
    #
    if (form.is_valid ( )):
        form.save (commit=True)
    return edit_vacancy (request)


@login_required
def delete_vacancy (request, id):
    """
    Deletes the vacancy with the received id.-
    """
    v = get_object_or_404 (Vacancy, pk=id)
    v.delete ( )
    return edit_vacancy (request)


@login_required
def invite_player (request, id):
    """
    Sends an invitation to another player for a tennis match.-
    """
    v = get_object_or_404 (Vacancy, pk=id)
    subject = '[%s] %s %s %s %s %s' % (_('Invitation'),
                                       v.get_day_display ( ),
                                       v.get_from_to_display ( ),
                                       v.get_hour_display ( ),
                                       _('in'),
                                       v.city)
    return user_messages.views.compose (request,
                                        recipient=v.player.user_profile.user.username,
                                        subject=subject)


def search_opponent (request, city_id=None):
    """
    Displays the search form to look for an opponent. It also displays
    the results of the search. When called with GET, random opponents 
    are displayed.-
    """
    #
    # exclude the player making the search
    #
    if request.user.is_authenticated ( ):
        player = UserProfile.objects.get_profile (request.user.username)
        if player.is_player ( ):
            vacancies = Vacancy.objects.exclude (player=player)
        else:
            vacancies = Vacancy.objects.all ( )
    else:
        vacancies = Vacancy.objects.all ( )
    
    if request.method == 'POST':
        #
        # search opponents, available on the same days and cities
        #
        form = SearchOpponentForm (request.POST, 
                                   label_suffix=' ')
        if form.is_valid ( ):
            when = [ form.cleaned_data['when'] ]
            where = form.cleaned_data['where'] if city_id is None else city_id 
            #
            # add filters by day
            #
            if ('XX' not in when):
                #
                # during week days?
                #
                if ('WD' in when):
                    when = when + Vacancy.get_weekdays ( )
                elif (form.cleaned_data['when'] in Vacancy.get_weekdays ( )):
                    when.append ('WD')
                #
                # during weekends?
                #
                if ('WN' in when):
                    when = when + Vacancy.get_weekends ( )
                elif (form.cleaned_data['when'] in Vacancy.get_weekends ( )):
                    when.append ('WN')
                vacancies = vacancies.filter (day__in=when)
            #
            # add filters by city
            #
            if (where is not None):
                vacancies = vacancies.filter (city=where)
            #
            # get the players matching the vacancies
            #
            players_qset = PlayerProfile.objects.filter (pk__in=vacancies.values_list('player_id')) 
    else:
        form = SearchOpponentForm (label_suffix=' ')
        #
        # display random player's vacancies, if any
        #
        players = vacancies.distinct ( ).values_list ('player_id')
        if players:
            rand_pl = random.randint (0, players.count ( ) - 1)
            players_qset = PlayerProfile.objects.filter (pk=players[rand_pl][0])
        else:
            players_qset = None

    return render_to_response ('players/opponent.html',
                               {'form': form,
                                'players_qset': players_qset},
                               context_instance=RequestContext(request))
