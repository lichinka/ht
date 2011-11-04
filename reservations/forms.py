import locale
from datetime import date, timedelta

from django import forms
from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceField
from django.forms.widgets import HiddenInput, DateInput
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.aggregates import Max

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
    repeat = forms.BooleanField (initial=False,
                                 required=False)
    repeat_until = forms.DateField ( )
    
    class Meta:
        model = Reservation

    def save (self, commit=True):
        """
        Creates weekly reservations, if the repeat flag is on, and
        repeat_until holds a valid date.-
        """
        #
        # first of all, try to save the first reservation of the series
        #
        r = super (ReservationForm, self).save (commit=False)
        #
        # find out if this is a repeating reservation
        #
        if self.cleaned_data['repeat']:
            series = Reservation.objects.exclude (repeat_series__isnull=True) \
                                        .aggregate (Max ('repeat_series'))
            if series['repeat_series__max']:
                series = int (series['repeat_series__max']) + 1
            else:
                series = 1
            r.repeat_series = series
            #
            # save one reservation for each date in the series
            #
            until_date = self.cleaned_data['repeat_until']
            repeat_dates = [self.cleaned_data['for_date']]
            while until_date > repeat_dates[-1]:
                next_date = repeat_dates[-1] + timedelta (days=7)
                repeat_dates.append (next_date)
            if repeat_dates[-1] > until_date:
                repeat_dates.pop ( )
            #
            # we've already added this one through 'r'
            #
            repeat_dates.remove (self.cleaned_data['for_date'])
            
            for d in repeat_dates:
                rr = Reservation.objects.create (created_on=r.created_on,
                                                 for_date=d,
                                                 type=r.type,
                                                 description=r.description,
                                                 user=r.user,
                                                 vacancy=r.vacancy,
                                                 repeat_series=r.repeat_series)
                rr.save ( )
        #
        # don't forget to save the original instance
        #
        if commit:
            r.save ( )
        return r

        
    def clean (self):
        """
        Checks that repeat_until is later than the first reservation date.-
        """
        cleaned_data = self.cleaned_data
        is_repeat = cleaned_data.get ('repeat')
        from_date = cleaned_data.get ('for_date')
        until_date = cleaned_data.get ('repeat_until')
        
        if is_repeat:
            if from_date > until_date:
                raise forms.ValidationError (_('Please check the dates!'))
        return cleaned_data
        

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
    