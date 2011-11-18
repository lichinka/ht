from django import template
from django.http import Http404

from clubs.models import CourtSetup, Vacancy
from accounts.models import UserProfile
from reservations.models import Reservation

register = template.Library ( )



@register.inclusion_tag('reservations/reservations_per_court.html')
def reservations_per_court (court_list, for_date, for_hour):
    """
    Renders available and reserved terms for the received date and
    hour, per court.-
    """
    dow = for_date.isoweekday ( )
    for court in court_list:
        court.vacancy = Vacancy.objects.get_all ([court], [dow], [for_hour])
        court.vacancy = court.vacancy[0]
        try:
            cs = court.court_setup
        except AttributeError:
            cs = CourtSetup.objects.get (pk=court['court_setup_id'])
        court.reservation = Reservation.objects.by_date (cs, for_date) \
                                               .filter (vacancy=court.vacancy)
        if court.reservation:
            court.reservation = court.reservation[0]
            
    return {'court_list': court_list,
            'ordinal_date': for_date.toordinal ( ),}


    
@register.inclusion_tag('reservations/reservation_count_per_club.html')
def reservation_count_per_club (user):
    """
    Renders a the number of active reservations for today,
    tomorrow and the whole week. It also provides links to
    the detailed reservation view.-
    """
    club = UserProfile.objects.get_profile (user.username)
    
    if club.is_club ( ):
        return {'today_count' : Reservation.objects.get_count_for_today ( ),
                'tomorrow_count': Reservation.objects.get_count_for_tomorrow ( ),
                'week_count' : Reservation.objects.get_count_for_week ( )}
    else:
        raise Http404
    