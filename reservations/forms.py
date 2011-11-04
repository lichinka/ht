import locale
from datetime import date, timedelta

from django import forms
from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceField
from django.forms.widgets import HiddenInput, DateInput
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from locations.models import City
from clubs.models import Vacancy
from reservations.models import Reservation



class ReservationForm (forms.ModelForm):
    """
    A form to create/edit reservations.-
    """
    created_on = forms.CharField (widget=HiddenInput ( ))
    type = forms.CharField (widget=HiddenInput ( ))
    user = ModelChoiceField (queryset=User.objects.all ( ),
                             widget=HiddenInput ( ))
    vacancy = ModelChoiceField (queryset=Vacancy.objects.all ( ),
                                widget=HiddenInput ( ))
    class Meta:
        model = Reservation
        
        

class SelectDateForm (forms.Form):
    """
    A form to select for which date to display reservations.-
    """
    for_date = forms.DateField (initial=date.today ( ))
    #
    # these three fields are hidden
    # we cannot use a HiddenInput, because it cannot handle date values
    #
    today_date = forms.DateField (initial=date.today ( ),
                                  widget=DateInput (format=locale.nl_langinfo(locale.D_FMT),
                                                    attrs={'style': 'display:none'}))
    prev_date = forms.DateField (initial=date.today ( ) - timedelta (days=1),
                                 widget=DateInput (format=locale.nl_langinfo(locale.D_FMT),
                                                   attrs={'style': 'display:none'}))
    next_date = forms.DateField (initial=date.today ( ) + timedelta (days=1),
                                 widget=DateInput (format=locale.nl_langinfo(locale.D_FMT),
                                                   attrs={'style': 'display:none'}))
    
    
    
class SearchFreeCourtForm (forms.Form):
    """
    A form to look for a free court and potentially make a reservation.-
    """
    #
    # set up the dates drop-down
    #
    today = date.today ( )
    tomorrow = today + timedelta (days=1)
    DATES = [(today.toordinal ( ), _('Today')),
             (tomorrow.toordinal ( ), _('Tomorrow'))]
    for d in range (2, 7):
        day_offset = timedelta (days=d)
        day = today + day_offset
        DATES.append ((day.toordinal ( ), 
                       date.strftime (day,
                                      locale.nl_langinfo (locale.D_FMT))))
    #
    # set up the times drop-down
    #
    TIMES = [('XX', _('-- anytime --')),
             ('AM', _('Morning')),
             ('PM', _('Afternoon')),
             ('EV', _('Evening'))]
    for k,v in Vacancy.HOURS[:-1]:
        TIMES.append ((str(k), v))
    #
    # set up the reservation length drop-down
    #   
    HOURS = ((1, _('1 hour')),
             (2, _('2 hours')),
             (3, _('3 hours')))
    
    location = ModelChoiceField (queryset=City.objects.all ( ).order_by ('name'),
                                 empty_label=_('-- anywhere --'),
                                 required=False)
    for_date = ChoiceField (choices=DATES,
                            initial=today)
    for_time = ChoiceField (choices=TIMES,
                            initial='XX')
    hours = ChoiceField (choices=HOURS,
                         initial=1)
    