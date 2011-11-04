from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from accounts.models import UserProfile
from locations.models import City



class SiteViewTest (TestCase):
    """ All the test cases for entry views of the site.-
    """
    T_CLUB = {'username': 'test_club',
              'email': 'club@nowhere.si',
              'password': 'averygoodpassword'}
    T_PLAYER ={'username': 'test_player',
               'email': 'player@nowhere.si',
               'password': 'thepasswordof1player'}
    
    def setUp (self):
        """
        Creates a club, player and a client used during testing.-
        """
        self.cli = Client ( )
        c = User.objects.create_user (**self.T_CLUB)
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")
        p = User.objects.create_user (**self.T_PLAYER)
        self.player = UserProfile.objects.create_player_profile (p.username)
        self.player.level = 'I'
        self.player.male = True
        self.player.right_handed = False
        self.player.save ( )
        
    def test_home (self):
        """ Checks the behavior of ht.views.home.-
        """
        view_url = reverse ('ht.views.home')
        
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template.name, 'welcome.html')
        
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'clubs/home.html')
        
        #
        # log the player in
        #
        self.cli.logout ( )
        self.cli.login (username=self.T_PLAYER['username'],
                        password=self.T_PLAYER['password'])
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'players/home.html')
        
        
        
class ViewTest (TestCase):
    """ All the test cases for the views of this app.-
    """
    def setUp (self):
        """
        Creates a client used during testing.-
        """
        self.cli = Client ( )
        
        
    def test_success (self):
        """ Checks the behavior of ht_utils.views.success.-
        """
        view_url = reverse ('ht_utils.views.success')
        response = self.cli.get (view_url)
        self.assertEquals (response.status_code, 200)
        self.assertEquals (response.template[0].name, 'ht_utils/success.html')
