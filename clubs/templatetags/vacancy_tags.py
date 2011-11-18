import locale

from django import template

from clubs.models import CourtSetup, Vacancy
from reservations.models import Reservation

register = template.Library ( )
    


@register.inclusion_tag ('clubs/vacancy_per_hour.html')
def vacancy_per_hour (court, for_date, hour_list):
    """
    Renders an table row with link buttons, containing the
    prices for the selected court and date (for_date), per
    hour in 'hour_list'. If a term is not free (i.e. it has
    already been booked), the '-' string is rendered instead.-
    """
    dow = for_date.isoweekday ( )
    hour_list = [{'value': k} for (k,v) in hour_list]
    
    for h in hour_list:
        h['vacancy'] = Vacancy.objects.get_all ([court], [dow], [h['value']])
        h['vacancy'] = h['vacancy'][0]
        try:
            cs = court.court_setup
        except AttributeError:
            cs = CourtSetup.objects.get (pk=court['court_setup_id'])
        h['reservation'] = Reservation.objects.by_date (cs, for_date) \
                                              .filter (vacancy=h['vacancy'])
        if h['reservation']:
            h['reservation'] = h['reservation'][0]
        else:
            h['reservation'] = None
            
    return {'hour_list': hour_list,
            'ordinal_date': for_date.toordinal ( ),}



@register.inclusion_tag('clubs/vacancy_prices_per_day.html')
def vacancy_prices_per_day (court, hour):
    """
    Renders an table row with input texts, containing the
    prices for the selected court, per hour and per day. If
    the selected term is not defined (i.e. it has no price),
    the '- - -' string is rendered instead.-
    """
    prices = []
    try:
        court_id = court['id']
    except TypeError:
        court_id = court.id
        
    vs = Vacancy.objects.filter (court__id=court_id) \
                        .filter (available_from=hour) \
                        .order_by ('day_of_week') \
                        .values ('id', 'price')
    for v in vs:
        price_name = 'price_%s' % str(v['id'])
        price_value = '- - -' if not v['price'] else locale.format ('%.2f', 
                                                                    v['price'], 
                                                                    monetary=True)
        prices.append ((price_name, price_value))
    return {'prices' : prices,}
