from ranking.models import Result
from accounts.models import PlayerProfile

from django import forms
from django.utils.translation import ugettext_lazy as _



class EnterSingleMatchResultForm (forms.Form):
    """
    A form to enter the result of a singles match.-
    """
    YES_NO = (('Y', _('Yes')),
              ('N', _('No')))
    user_won = forms.TypedChoiceField (choices=YES_NO,
                                       label=_('Did you win?'),
                                       widget=forms.widgets.RadioSelect ( ))
    type = forms.TypedChoiceField (choices=Result.TYPES,
                                   initial=3)
    score = forms.RegexField (regex='\d{1,2}%s\d{1,2}%s*' % (Result.GAMES_DELIMITER,
                                                             Result.SETS_DELIMITER))

    def __init__ (self, *args, **kwargs):
        """
        Custom constructor to create an opponent list, 
        excluding user currently logged-in.-
        """
        usr = kwargs.pop ('usr') if 'usr' in kwargs.keys ( ) else None
        super (EnterSingleMatchResultForm, self).__init__(*args, **kwargs)
        queryset = PlayerProfile.get_players ( ).exclude (id=usr.id) \
                   if usr else PlayerProfile.get_players ( )
        #
        # the opponent field should be displayed first
        #
        self.fields.insert (0, 
                            'opponent',
                            forms.ModelChoiceField (queryset=queryset))

    def clean (self):
        """
        Makes sure the score entered fits the match type.-
        """
        sets = list ( )
        data = self.cleaned_data
        type = data['type']
        score = data['score']
       
        for m in self.fields['score'].regex.finditer (score):
            sets.append (m.group ( ))
        #
        # we expect a different score, depending on
        # the number sets actually played
        #
        if int(type) == len(sets):
            pass
        elif (int(type) == 3) and (len(sets) == 2):
            pass
        elif (int(type) == 5) and (len(sets) in [3, 4]):
            pass
        else:
            raise forms.ValidationError (_('The entered score does not fit the match type.'))
        
        return data
    