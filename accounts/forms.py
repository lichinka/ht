from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from accounts.models import PlayerProfile
from django.forms import widgets



class EditPlayerProfileForm (forms.ModelForm):
    """
    A form to edit the player's profile.-
    """
    user = forms.ModelChoiceField (queryset=User.objects.all ( ),
                                   widget=widgets.HiddenInput ( ))
    first_name = forms.CharField (max_length=30)
    last_name = forms.CharField (max_length=30)
    next = forms.CharField (widget=widgets.HiddenInput ( ),
                            required=False)
    class Meta:
        model = PlayerProfile
        
        
        
class RegisterUserForm (forms.Form):
    """
    A form to register a new user.-
    """
    email = forms.EmailField ( )
    pass1 = forms.CharField (max_length=30,
                             widget=forms.PasswordInput ( ))
    pass2 = forms.CharField (max_length=30,
                             widget=forms.PasswordInput ( ))
   
    def clean_email (self):
        """
        Checks that the email does not yet exist, since
        we use it as user name for players.-
        """
        data = self.cleaned_data['email']
        try:
            User.objects.get (username=data)
            raise forms.ValidationError (_('Please choose a different email address'))
        except ObjectDoesNotExist:
            pass
        return data

    def clean (self):
        """
        Checks that both password entries match.-
        """
        cleaned_data = self.cleaned_data
        pass1 = cleaned_data.get ('pass1')
        pass2 = cleaned_data.get ('pass2')
        if pass1 != pass2:
            raise forms.ValidationError (_('Passwords do not match, please retype them'))
        return cleaned_data
