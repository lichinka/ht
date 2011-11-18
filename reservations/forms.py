import locale
from datetime import date, timedelta

from django import forms
from django.forms.fields import ChoiceField
from django.forms.models import ModelChoiceField
from django.forms.widgets import HiddenInput, DateInput
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.aggregates import Max

from clubs.models import CourtSetup, Vacancy
from locations.models import City
from reservations.models import Reservation
from django.core.exceptions import ObjectDoesNotExist




class TransferOrDeleteForm (forms.Form):
    #
    # what to do with reservations
    #   
    TRANS_OR_DEL = ((1, _('Transfer all reservations')),
                    (2, _('Delete all reservations')),
                    (3, _('Cancel this action')))
    user_choice = forms.ChoiceField (choices=TRANS_OR_DEL,
                                     initial=1)
    transfer_to = forms.ModelChoiceField (queryset=CourtSetup.objects.none ( ),
                                          required=False)
    
    def clean (self):
        """
        Checks that 'transfer_to' is selected if an action that
        depends on it has been selected.-
        """
        cleaned_data = self.cleaned_data
        user_choice = cleaned_data.get ('user_choice')
        if int(user_choice) == 1:
            try:
                CourtSetup.objects.get (pk=cleaned_data.get ('transfer_to'))
            except ObjectDoesNotExist:
                raise forms.ValidationError (_('Please select a valid court setup!'))
        return cleaned_data
    

class ReservationForm (forms.ModelForm):
    """
    A form to create/edit reservations.-
    """
    created_on = forms.CharField (widget=HiddenInput ( ))
    for_date = forms.DateField (widget=DateInput (attrs={'readonly': 'readonly'}))
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
        # first of all, try to save the first reservation
        #
        r = super (ReservationForm, self).save (commit=False)
        #
        # find out if this is a repeating reservation
        #
        if self.cleaned_data['repeat']:
            #
            # get the staring and ending dates
            #
            from_date = self.cleaned_data['for_date']
            until_date = self.cleaned_data['repeat_until']
            #
            # the first reservation of the series is 'r',
            # so we don't want to add it twice
            #
            from_date += timedelta (days=7)
            #
            # there should be one more reservation at least
            #
            new_res_count = Reservation.objects.get_weekly_reservation_count (from_date, 
                                                                              until_date)
            if new_res_count > 0:
                #
                # check that all terms are free
                #
                booked = Reservation.objects.book_weekly (from_date, 
                                                          until_date,
                                                          commit=False,
                                                          created_on=r.created_on,
                                                          type=r.type,
                                                          description=r.description,
                                                          user=r.user,
                                                          vacancy=r.vacancy)
                if new_res_count == len(booked):
                    #
                    # there is place for all reservations, save the to the DB
                    #
                    booked = Reservation.objects.book_weekly (from_date, 
                                                              until_date,
                                                              commit=True,
                                                              created_on=r.created_on,
                                                              type=r.type,
                                                              description=r.description,
                                                              user=r.user,
                                                              vacancy=r.vacancy)
                    #
                    # the repeating series identifier for the first reservation
                    #
                    r.repeat_series = booked[0].repeat_series
                else:
                    #
                    # not all terms are free
                    #
                    raise ValueError (_("No free terms for all reservations"))
        #
        # don't forget to save the original instance
        #
        if commit:
            r.save ( )
        return r

        
    def clean (self):
        """
        Checks that repeat_until is later than the first reservation date.
        If repeat weekly is on, the description should be given.-
        """
        cleaned_data = self.cleaned_data
        is_repeat = cleaned_data.get ('repeat')
        from_date = cleaned_data.get ('for_date')
        until_date = cleaned_data.get ('repeat_until')
        description = cleaned_data.get ('description')
        
        if is_repeat:
            if from_date > until_date:
                raise forms.ValidationError (_('Please check the dates!'))
            if (len(description) == 0) or (description.isspace ( )):
                raise forms.ValidationError (_('This field is required'))
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
    
