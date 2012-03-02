from django import forms
from django.contrib.auth.models import User

from accounts.models import PlayerProfile, ClubProfile



class EditUserLoginData (forms.ModelForm):
    """
    A form to edit the user's email address.-
    """
    def __init__(self, *args, **kwargs):
        """
        A custom constructor to make the 'username' field read-only.-
        """
        super (EditUserLoginData, self).__init__ (*args, **kwargs)
        instance = getattr (self, 'instance', None)
        if instance and instance.id:
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['disabled'] = True

    def clean_username (self):
        """
        Avoids any possible change in the read-only field 'username',
        before POST or GET.-
        """
        return self.instance.username
    
    class Meta:
        model = User
        fields = ('username', 'email')
       
        
    
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
