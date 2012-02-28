from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from accounts.models import PlayerProfile, ClubProfile




class EditClubProfileForm (forms.ModelForm):
    """
    A form to edit the club's profile.-
    """
    class Meta:
        model = ClubProfile
        fields = ('company', 'address', 'city', 'tax_number', 'phone',
                  'representative', 'representative_title')


class EditPlayerProfileForm (forms.ModelForm):
    """
    A form to edit the player's profile.-
    """
    first_name = forms.CharField (max_length=30)
    last_name = forms.CharField (max_length=30)
    
    class Meta:
        model = PlayerProfile
        fields = ('male', 'right_handed', 'level')
