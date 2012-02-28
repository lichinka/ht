import sys
import random
from datetime import date

from django.db import models
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from accounts.models import UserProfile, PlayerProfile
from locations.models import City
from reservations.models import Reservation



class BaseViewTestCase (TestCase):
    """
    A base class for test cases of views.-
    """
    T_ROOT = {'username': 'superman',
              'email'   : 'superman@kripton.si',
              'password': 'ineednopassword'}
    T_CLUB = {'username'             : 'test_club',
              'email'                : 'club@nowhere.si',
              'password'             : 'averygoodpassword',
              'company'              : 'The best tennis club d.o.o.',
              'address'              : 'Postal address 1231',
              'city'                 : None,
              'tax_number'           : 'SI1112223344',
              'telephone'            : '111-222-333',
              'representative'       : 'Al Gore',
              'representative_title' : 'Vicepresident',}
    T_PLAYER = {'username'    : 'test_player',
                'email'       : 'player@nowhere.si',
                'password'    : 'thepasswordof1player',
                'first_name'  : 'Andre',
                'last_name'   : 'Agassi',
                'level'       : random.choice (PlayerProfile.LEVELS)[0],
                'male'        : random.randint (1, 2) % 2 == 0,
                'right_handed': random.randint (1, 9) % 3 == 0}

    # This attribute indicates whether the current test case
    # runs within its own transaction (the default) or not.
    own_transaction = True

    # An attribute with a valid superuser
    root = None

    # An attribute holding a reference to a valid club profile
    club = None

    # An attribute holding a reference to a valid player profile
    player = None

    # An attribute containing a list of randomly-generated
    # court setups
    cs_list = []

    # An attribute containing a list of randomly-generated
    # vacancies
    vacancy_list = []

    # An attribute containing a list of randomly-generated
    # reservations
    res_list = []

    def __init__ (self, methodName='runTest', own_transaction=True):
        """
        Initializes this test case, optionally turning transaction
        support off, thus enabling test-case reuse.-
        """
        super (BaseViewTestCase, self).__init__ (methodName)
        self.own_transaction = own_transaction

    def _fixture_setup (self):
        """
        Creates a transaction, within which the test is run.-
        """
        if self.own_transaction:
            super (BaseViewTestCase, self)._fixture_setup ( )
        else:
            sys.stdout.write ('\n\tSkipping transaction creation\n')

    def _fixture_teardown(self):
        """
        Rolls the transaction back, to give the next test case
        the same initial state.-
        """
        if self.own_transaction:
            super (BaseViewTestCase, self)._fixture_teardown ( )
        else:
            sys.stdout.write ('\n\tSkipping transaction creation\n')

    def _create_superuser (self):
        """
        Creates a superuser.-
        """
        self.root = User.objects.create_superuser (**self.T_ROOT)

    def _create_club (self):
        """
        Creates a club.-
        """
        c = User.objects.create_user (username=self.T_CLUB['username'],
                                      email=self.T_CLUB['email'],
                                      password=self.T_CLUB['password'])
        #
        # this cannot happen before, otherwise the 'City'
        # table does not exist
        #
        self.T_CLUB['city'] = random.choice (City.objects.all ( ))
        self.club = UserProfile.objects.create_club_profile (c,
                                                             self.T_CLUB['address'],
                                                             self.T_CLUB['city'],
                                                             self.T_CLUB['telephone'],
                                                             self.T_CLUB['company'])

    def _create_player (self):
        """
        Creates a player.-
        """
        p = User.objects.create_user (username=self.T_PLAYER['username'],
                                      password=self.T_PLAYER['password'],
                                      email=self.T_PLAYER['email'])
        p.first_name = self.T_PLAYER['first_name']
        p.last_name = self.T_PLAYER['last_name']
        p.save ( )
        self.player = UserProfile.objects.get_profile (self.T_PLAYER['username'])
        self.player.level = self.T_PLAYER['level']
        self.player.male = self.T_PLAYER['male']
        self.player.right_handed = self.T_PLAYER['right_handed']
        self.player.save ( )

    def _add_court_setups (self):
        """
        Adds a couple of extra court setups to the default club.-
        """
        from clubs.models import CourtSetup
        #
        # we need a club!
        #
        self._create_club ( )

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
        self.cs_list.append (CourtSetup.objects.create (name="The fifth court setup",
                                                        club=self.club,
                                                        is_active=False))
        #
        # activate a random court setup
        #
        CourtSetup.objects.activate (random.choice (self.cs_list))

    def _add_courts (self):
        """
        Adds a random number of courts to each court setup.-
        """
        from clubs.models import Court
        #
        # we need at least one court setup
        #
        self._add_court_setups ( )

        for cs in self.cs_list:
            for i in range (2, random.randint (2, 7)):
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
        from clubs.models import Court, Vacancy
        #
        # we need at least one court
        #
        self._add_courts ( )

        self.vacancy_list = []
        for cs in self.cs_list:
            courts = Court.objects.get_available (cs)
            for c in courts.iterator ( ):
                court_vacancy_terms = Vacancy.objects.get_all ([c])
                for v in court_vacancy_terms.iterator ( ):
                    v.price = '%10.2f' % float ((10*c.id + v.id) % 1000)
                    v.save ( )
                    self.vacancy_list.append (v)


    def _add_reservations (self, court_setup=None):
        """
        Create some random reservations to the received court setup.-
        """
        from clubs.models import Vacancy
        #
        # we need at least one vacancy price
        # and a player
        #
        self._create_player ( )
        self._add_vacancy_prices ( )
        #
        # select random court setups or the one given
        #
        res_cs_list = list ( )
        if court_setup is None:
            for i in range (0, random.randint (1, len (self.cs_list))):
                res_cs_list.append (self.cs_list[i])
        else:
            res_cs_list.append (court_setup)
        for cs in res_cs_list:
            self.res_list = list ( )
            for i in range (0, random.randint (1, 10)):
                v = None
                while v is None:
                    for_date = date.today ( )
                    hour = random.choice (Vacancy.HOURS)
                    v = Vacancy.objects.get_free (cs, for_date, hour[0]).values ('id')
                    v = random.choice (v) if v else None
                v = Vacancy.objects.get (pk=v['id'])
                self.res_list.append (Reservation.objects.create (for_date=date.today ( ),
                                                                  type='P' if i%2 == 0 else 'C',
                                                                  description="Test reservation %s" % str(i),
                                                                  user=self.player.user if i%2 == 0 else self.club.user,
                                                                  vacancy=v))

    def setUp (self):
        """
        Creates a superuser, club, player and a client, fills prices
        for some vacancy terms and creates reservations used during testing.-
        """
        #
        # backward compatibility name of the test client
        #
        self.cli = self.client
        self._create_superuser ( )
        self._add_reservations ( )
        #
        # mark some used members as empty
        #
        self.view_path = None
        self.template_name = None


    def _test_only_player_has_access (self, view_args=None):
        self._test_only_user_has_access (self.T_PLAYER['username'],
                                         self.T_PLAYER['password'],
                                         view_args)
        
    def _test_only_club_has_access (self, view_args=None):
        self._test_only_user_has_access (self.T_CLUB['username'],
                                         self.T_CLUB['password'],
                                         view_args)
        
    def _test_only_user_has_access (self, username, password, view_args=None):
        """
        Tests this view is only accessible by a the user whose credentials
        were given. This function accepts appending 'view_args' to the URL of
        the view.-
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
        resp = self.client.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'accounts/login.html')
        #
        # check other profiles do not have access
        #
        profile = UserProfile.objects.get_profile (username)
        if profile.is_club ( ):
            self.client.login (username=self.T_PLAYER['username'],
                               password=self.T_PLAYER['password'])
        elif profile.is_player ( ):
            self.client.login (username=self.T_CLUB['username'],
                               password=self.T_CLUB['password'])
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.client.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 404)
        #
        # log a user in, using the received information
        #
        self.client.login (username=username,
                           password=password)
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.client.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertTemplateUsed (resp, self.template_name)

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
            self.client.login (username=login_info['username'],
                               password=login_info['password'])
        #
        # test the view
        #
        self.assertIsNotNone (self.view_path)
        self.assertIsNotNone (self.template_name)
        view_url = reverse (self.view_path,
                            args=view_args)
        resp = self.client.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, self.template_name)
    
       
    def _test_multiple_model_instances_save (self, instance_data, form_name='form'): 
        """
        Tests that data from multiple models are correctly saved via a view.
        This method returns the last 'response' object used, after all 
        assertions of the last model checked are successful.
       
            instance_data: a list containing a two-level dictionary with the
                           instances (key 'instance') and the data (key 'data')
                           against which they have to be checked, e.g.
                           
                           [{'instance': self.club.user,
                             'data':     {'first_name': 'Pepe',
                                          'last_name' : 'Gomez'}},
                            ...]
                                         
                           instance_data['data'] is a dictionary which keys 
                           are field names of the instance held in 
                           instance_data['instance'];
                form_name: the name of the form included in the tested view,
                           defaults to 'form'.-
              
        """
        for model in instance_data:
            resp = self._test_model_instance_save (model['instance'],
                                                   model['data'],
                                                   form_name)
        return resp
            
    def _test_model_instance_save (self, instance, data, tested_fields=None,
                                   form_name='form'):
        """
        Tests that a model data is correctly saved via a view. This method
        returns the 'response' object used, after all assertions have been
        successful.
        
                 instance: the instance object to test;
                     data: a dictionary which keys are field names of the
                           tested instance;
            tested_fields: a tuple of field names that are to be tested.
                           It defaults to test all the fields (i.e. keys) 
                           of the 'data' dictionary;
                form_name: the name of the form included in the tested view,
                           defaults to 'form'.-
              
        """
        try:
            if tested_fields is None:
                tested_fields = data.keys ( )
        except AttributeError:
            raise AttributeError ("Parameter 'data' should be a dictionary.")
        
        resp = self.client.post (reverse (self.view_path), data, follow=True)
        #
        # inspect the form object, if it is available
        #
        try:
            form = resp.context[-1][form_name]
            if len (form.errors) > 0:
                sys.stderr.write ("The form '%s' has validation errors:\n" % form_name)
                for f in form.errors.keys ( ):
                    sys.stderr.write ('\t%s -> %s\n' % (f, form.errors[f]))
            self.assertEquals (len (form.errors), 0)
        except KeyError:
            #
            #sys.stderr.write ("*** WARNING: Form '%s' not found in view '%s'\n" % (form_name,
            #                                                                       view_url))
            pass
        #
        # load fresh instance data from the DB
        #
        if isinstance (instance, models.Model):
            pk = instance.pk
            instance_model = instance.__class__
            instance = instance_model.objects.get (pk=pk)
        else:
            raise TypeError ("Instance '%s' is not a Model." % str (instance))
        #
        # check saved data is correct
        #
        for field in tested_fields:
            field_data = getattr (instance, field, None) 
            #
            # foreign-keys are compared by model instance
            #
            if isinstance (field_data, models.Model):
                fk_model    = field_data.__class__
                data[field] = fk_model.objects.get (pk=int (data[field]))
                self.assertEquals (field_data, data[field])
            else:
                #
                # other fields are compared by their unicode representation
                #
                self.assertEquals (unicode (field_data), unicode (data[field]))
        return resp


        
class HomeViewTest (BaseViewTestCase):
    """
    All the test cases for home page of the site.-
    """
    def test_guests_should_be_redirected_to_welcome (self):
        view_url = reverse ('ht.views.home')
        #
        # unauthenticated users should see the welcome screen
        #
        resp = self.client.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template.name, 'welcome.html')

    def test_superuser_not_allowed_in_the_public_site (self):
        view_url = reverse ('ht.views.home')
        #
        # superusers should not be allowed in this site
        #
        self.client.logout ( )
        self.client.login (username=self.T_ROOT['username'],
                        password=self.T_ROOT['password'])
        resp = self.client.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template.name, 'superuser_not_allowed.html')

    def test_clubs_redirected_to_their_home_page (self):
        view_url = reverse ('ht.views.home')
        #
        # log the club in
        #
        self.client.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        resp = self.client.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'clubs/home.html')

    def test_players_redirected_to_their_home_page (self):
        view_url = reverse ('ht.views.home')
        #
        # log the player in
        #
        self.client.logout ( )
        self.client.login (username=self.T_PLAYER['username'],
                        password=self.T_PLAYER['password'])
        resp = self.client.get (view_url)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'players/home.html')
