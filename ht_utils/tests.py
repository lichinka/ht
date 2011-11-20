from random import randint
from datetime import date

from django.conf import settings
from django.test import TestCase
from django.db.utils import IntegrityError
from django.test.client import Client
from django.test.simple import DjangoTestSuiteRunner
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from ht_utils import pick_random_element
from clubs.models import CourtSetup, Court, Vacancy
from accounts.models import UserProfile
from locations.models import City
from reservations.models import Reservation



class BaseViewTestCase (TestCase):
    """
    A base class for test cases of views.-
    """
    T_ROOT = {'username': 'superman',
              'email': 'superman@kripton.si',
              'password': 'ineednopassword'}
    T_CLUB = {'username': 'test_club',
              'email': 'club@nowhere.si',
              'password': 'averygoodpassword'}
    T_PLAYER ={'username': 'test_player',
               'email': 'player@nowhere.si',
               'password': 'thepasswordof1player'}
    
    def _create_superuser (self):
        """
        Creates a superuser.-
        """
        self.root = User.objects.create_superuser (**self.T_ROOT)
        
    def _create_club (self):
        """
        Creates a club.-
        """
        c = User.objects.create_user (**self.T_CLUB)
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")
        
    def _create_player (self):
        """
        Creates a player.-
        """
        p = User.objects.create_user (**self.T_PLAYER)
        p.first_name = 'Andre'
        p.last_name = 'Agassi'
        p.save ( )
        self.player = UserProfile.objects.create_player_profile (p.username)
        self.player.level = 'I'
        self.player.male = True
        self.player.right_handed = False
        self.player.save ( )
    
    def _add_court_setups (self):
        """
        Adds a couple of extra court setups to the default club.-
        """
        self.cs_list = list ( )
        self.cs_list.append (CourtSetup.objects.get_active (self.club))
        self.cs_list.append (CourtSetup.objects.create (name="The second court setup",
                                                        club=self.club,
                                                        is_active=False))
        self.cs_list.append (CourtSetup.objects.create (name="The third court setup",
                                                        club=self.club,
                                                        is_active=False))
        self.cs_list.append (CourtSetup.objects.create (name="The fourth court setup",
                                                        club=self.club,
                                                        is_active=False))
    
    def _add_courts (self):
        """
        Adds a random number of courts to each court setup.-
        """
        for cs in self.cs_list:
            for i in range (2, randint (2, 7)):
                Court.objects.create (court_setup=cs,
                                      number=i,
                                      indoor=True if i%2 == 0 else False,
                                      light=False if i%2 == 0 else True,
                                      surface=Court.SURFACES[i%5][0],
                                      single_only=True if i%2 == 0 else False,
                                      is_available=False if i%2 == 0 else True)
        
    def _add_vacancy_prices (self):
        """
        Set some prices for the vacancy terms of all
        courts in all court setups.-
        """
        for cs in self.cs_list:
            courts = Court.objects.get_available (cs)
            for c in range (0, len(courts)):
                court_vacancy_terms = Vacancy.objects.get_all ([courts[c]])
                for v in range (0, len(court_vacancy_terms)):
                    court_vacancy_terms[v].price = '%10.2f' % float (10*c + v);
                    court_vacancy_terms[v].save ( )
    
    def _add_reservations (self, cs):
        """            
        Create some random reservations to the received court setup.-
        """
        self.res_list = list ( )
        courts = Court.objects.get_available (cs).values ( )
        for i in range (0, 10):
            if randint(0, 1) > 0:
                v = False
                while not v:
                    v = Vacancy.objects.get_all_by_date (courts,
                                                         [date.today ( )],
                                                         [pick_random_element (Vacancy.HOURS)[0]])
                try:
                    self.res_list.append (Reservation.objects.create (for_date=date.today ( ),
                                                                      type='P',
                                                                      description="Test reservation %s" % str(i),
                                                                      user=self.player.user if i%2 == 0 else self.club.user,
                                                                      vacancy=v[0]))
                except IntegrityError:
                    pass
                
    def setUp (self):
        """
        Creates a superuser, club, player and a client, fills prices
        for some vacancy terms and creates reservations used during testing.-
        """
        self.cli = self.client
        self._create_superuser ( )
        self._create_club ( )
        self._create_player ( )
        self._add_court_setups ( )
        self._add_courts ( )
        self._add_vacancy_prices ( )
        self._add_reservations (CourtSetup.objects.get_active (self.club))
        #
        # mark some used members as empty
        #
        self.view_path = None
        self.template_name = None

    def _test_only_club_has_access (self, login_info=None, view_args=None):
        """
        Tests this view is only accessible by a club,
        optionally logging a club in using the received info,
        and appending 'view_args' to the URL of the view.-
        """
        #
        # an anonymous user should not have access
        # since she/he must be redirected to the login page
        #
        self.client.logout ( )
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'accounts/login.html')
        #
        # a player should not have access
        # since she/he must receive the 'not found' page
        #
        self.client.login (username=self.T_PLAYER['username'], 
                           password=self.T_PLAYER['password'])
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 404)
        #
        # only a club should have access
        #
        if login_info is not None:
            #
            # log a user in, using the received information
            #
            self.cli.login (username=login_info['username'], 
                            password=login_info['password'])
        else:
            self.client.login (username=self.T_CLUB['username'], 
                               password=self.T_CLUB['password'])
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, self.template_name)
        
    def _test_existance_and_correct_template (self, login_info=None, view_args=None):
        """
        Tests the existance and correct rendering of the view,
        optionally logging a user in using the received info,
        and appending 'view_args' to the URL of the view.-
        """
        self.client.logout ( )
        if login_info is not None:
            #
            # log a user in, using the received information
            #
            self.cli.login (username=login_info['username'], 
                            password=login_info['password'])
        #
        # test the view
        #
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, self.template_name)
        


class AdvancedTestSuiteRunner (DjangoTestSuiteRunner):
    """
    A custom test suite to avoid running tests of applications
    specified in settings.TEST_EXCLUDE.-
    """
    EXCLUDED_APPS = getattr (settings, 'TEST_EXCLUDE', [])
    
    def __init__(self, *args, **kwargs):
        super (AdvancedTestSuiteRunner, self).__init__ (*args, **kwargs)
    
    def build_suite (self, *args, **kwargs):
        suite = super (AdvancedTestSuiteRunner, self).build_suite (*args, **kwargs)
        if not args[0] and not getattr(settings, 'RUN_ALL_TESTS', False):
            tests = []
            for case in suite:
                pkg = case.__class__.__module__.split('.')[0]
                if pkg not in self.EXCLUDED_APPS:
                    tests.append (case)
            suite._tests = tests 
        return suite
    

class HomeViewTest (BaseViewTestCase):
    """
    All the test cases for home page of the site.-
    """
    def test_guests_should_be_redirected_to_welcome (self):
        view_url = reverse ('ht.views.home')
        #
        # unauthenticated users should see the welcome screen
        #
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template.name, 'welcome.html')
        
    def test_superuser_not_allowed_in_the_public_site (self):
        view_url = reverse ('ht.views.home')
        #
        # superusers should not be allowed in this site
        #
        self.cli.logout ( )
        self.cli.login (username=self.T_ROOT['username'],
                        password=self.T_ROOT['password'])
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template.name, 'superuser_not_allowed.html')
        
    def test_clubs_redirected_to_their_home_page (self):
        view_url = reverse ('ht.views.home')
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'clubs/home.html')
    
    def test_players_redirected_to_their_home_page (self):
        view_url = reverse ('ht.views.home')
        #
        # log the player in
        #
        self.cli.logout ( )
        self.cli.login (username=self.T_PLAYER['username'],
                        password=self.T_PLAYER['password'])
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'players/home.html')
        
        
        
class SuccessViewTest (BaseViewTestCase):
    """
    Test cases for ht_utils.views.success.-
    """
    def test_existance_and_correct_template (self):
        view_url = reverse ('ht_utils.views.success')
        response = self.cli.get (view_url)
        self.assertEquals (response.status_code, 200)
        self.assertEquals (response.template[0].name, 'ht_utils/success.html')
