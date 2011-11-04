from django import forms

from clubs.models import CourtSetup, Court
from accounts.models import ClubProfile



class EditCourtSetupForm (forms.ModelForm):
    """
    A form to add/change a court setup.-
    """
    club = forms.ModelChoiceField (queryset=ClubProfile.objects.all ( ),
                                   widget=forms.widgets.HiddenInput ( )) 
    class Meta:
        model = CourtSetup
       
        
class EditCourtPropertiesForm (forms.ModelForm):
    """
    A form to edit the court properties (e.g. surface, light, ...).-
    """
    court_setup = forms.ModelChoiceField (queryset=CourtSetup.objects.all ( ),
                                          widget=forms.widgets.HiddenInput ( ))
    class Meta:
        model = Court
        