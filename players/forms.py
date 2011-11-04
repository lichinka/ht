from django import forms
from django.forms.models import ModelChoiceField
from django.forms.widgets import HiddenInput
from django.utils.translation import ugettext_lazy as _

from players.models import Vacancy
from accounts.models import PlayerProfile
from locations.models import City



class SearchOpponentForm (forms.Form):
    """
    A form to look for an opponent.-
    """
    WHEN_CHOICES = list (Vacancy.DAYS)
    WHEN_CHOICES.insert (0, ('XX', _('-- any day --')))
    when = forms.TypedChoiceField (choices = WHEN_CHOICES,
                                   initial='XX',
                                   required=False)
    where = forms.ModelChoiceField (queryset=City.objects.all ( ),
                                    empty_label=_('-- anywhere --'),
                                    required=False)
        
        
class EditVacancyForm (forms.ModelForm):
    """
    A form to add/change a player's vacancy.-
    """
    player = ModelChoiceField (queryset=PlayerProfile.objects.all ( ),
                               widget=HiddenInput ( ))
    class Meta:
        model = Vacancy
        widgets = {'from_to': forms.widgets.RadioSelect ( ),}
        
