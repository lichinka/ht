from django import template
from django.http import Http404

from accounts.models import UserProfile
from reservations.models import Reservation

register = template.Library ( )



@register.inclusion_tag ('reservations/reservations_per_day.html')
def reservations_per_day (terms, for_date, for_hour):
    """
    Renders free and booked terms for all the available courts
    in the received court setup, for the given date and hour.
    Terms is a multidimensional dictionary with the same structure
    as the data being displayed:
    
        terms[date][hour][court_id]['vacancy'] = Vacancy object
    
    and if the vacancy term is booked:
    
        terms[date][hour][court_id]['reservation'] = Reservation object
    """
    term_list = terms[for_date][for_hour]
    term_list = [(term_list[k]['vacancy'], term_list[k]['reservation']) for k in term_list.keys ( )]
    term_list = sorted (term_list, key=lambda e: e[0].court.number)
    return {'for_date': for_date,
            'for_hour': for_hour,
            'term_list': term_list}


    
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
    