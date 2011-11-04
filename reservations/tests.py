from random import randint
from datetime import date, datetime, timedelta

from django.test import TestCase
from django.test.client import Client
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models.deletion import ProtectedError
from django.contrib.auth.models import User

from clubs.models import CourtSetup, Court, Vacancy
from accounts.models import UserProfile
from locations.models import City
from reservations.models import Reservation



class ReservationTest (TestCase):
    """
    All the test cases for the Reservation model.-
    """
    T_CLUB = {'username': 'test_club',
              'email': 'club@nowhere.si',
              'password': 'averygoodpassword'}
    T_PLAYER ={'username': 'test_player',
               'email': 'player@nowhere.si',
               'password': 'thepasswordof1player'}
    
    
    def setUp (self):
        """
        Creates a club, player and a client, and fills prices
        for some vacancy terms used during testing.-
        """
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
        
        
    def test_default_type_is_player (self):
        """
        The default reservation type should be 'by player'.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        c = Court.objects.get_available (cs)
        for i in range (0, randint (1, 5)):
            v = Vacancy.objects.get_all ([c[0]], [Vacancy.DAYS[i][0]])
            r = Reservation.objects.create (for_date=date.today ( ),
                                            description="Test reservation",
                                            user=self.player.user,
                                            vacancy=v[i])
            r.save ( )
            r = Reservation.objects.get (pk=r.id)
            self.assertEquals (r.type, 'P')
            
                
    def test_cannot_delete_reserved_vacancy (self):
        """
        A reservation cannot be deleted indirectly by deleting the 
        referenced vacancy.-
        """
        #
        # create some random reservations
        #
        cs = CourtSetup.objects.get_active (self.club)
        c = Court.objects.get_available (cs)
        for i in range (0, randint (1, 15)):
            v = Vacancy.objects.get_all ([c[0]], [Vacancy.DAYS[i%7][0]])
            Reservation.objects.create (for_date=date.today ( ),
                                        description="Test reservation",
                                        user=self.player.user,
                                        vacancy=v[i])
        #
        # try to delete them indirectly via their referenced vacancies
        # (should throw ProtectedError exception)
        #
        v_ids = Reservation.objects.filter (user=self.player.user) \
                                   .values ('vacancy__id')
        for v in v_ids:
            try:
                Vacancy.objects.get (pk=v['vacancy__id']).delete ( )
                self.assertTrue (False)
            except ProtectedError:
                self.assertTrue (True)
            
            
                
class ViewTest (TestCase):
    """
    All the test cases for the views of this app.-
    """
    T_CLUB = {'username': 'test_club',
              'email': 'club@nowhere.si',
              'password': 'averygoodpassword'}
    T_PLAYER ={'username': 'test_player',
               'email': 'player@nowhere.si',
               'password': 'thepasswordof1player'}
    
    
    def setUp (self):
        """
        Creates a club, player and a client, and fills prices
        for some vacancy terms used during testing.-
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
        #
        # add some extra courts
        #
        cs = CourtSetup.objects.get_active (self.club)
        for i in range (3, randint (3, 15)):
            Court.objects.create (court_setup=cs,
                                  number=i,
                                  indoor=False if i%2==0 else True,
                                  light=True if i%2==0 else False,
                                  surface=Court.SURFACES[i%5][0],
                                  single_only=False if i%2==0 else True,
                                  is_available=True if i%2==0 else False)
        #
        # set some prices for the vacancy terms of all
        # courts in the active court setup
        #
        self.courts = Court.objects.get_available (cs)
        for i in range (0, len(self.courts)):
            court_vacancy_terms = Vacancy.objects.get_all ([self.courts[i]])
            for v in range (0, len(court_vacancy_terms)):
                court_vacancy_terms[v].price = '%10.3f' % float (10*i + v);
                court_vacancy_terms[v].save ( )
                
        
    def test_search (self):
        """
        Checks the behavior of reservations.views.search.-
        """
        view_url = reverse ('reservations.views.search')
        #
        # log the player in
        #
        self.cli.login (username=self.T_PLAYER['username'],
                        password=self.T_PLAYER['password'])
        response = self.cli.get (view_url)
        self.assertEquals (response.status_code, 200)
        self.assertEquals (response.template[0].name, 'reservations/search.html')
        response = self.cli.post (view_url,
                                  {'for_date': date.today ( ).toordinal ( ),
                                   'for_time': 'PM',
                                   'hours'   : 1})
        self.assertEquals (response.status_code, 200)
        form = response.context[-1]['form']
        self.assertEquals (len (form.errors), 0)
        self.assertEquals (response.template[0].name, 'reservations/user_view.html')

    
    def test_club_edit (self):
        """
        Checks the behavior of reservations.views.club_edit.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # randomly select some vacancies and reserve them by club
        #
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( ))
        for i in range (0, randint (0, 10)):
            v = all_vacancies[i]
            for_date = date.today ( ) + timedelta (days=i%7)
            view_url = reverse ('reservations.views.club_edit',
                                args=[v.id, for_date.toordinal ( )])
            #
            # correctly display the reservation form
            #
            resp = self.cli.get (view_url)
            self.assertEquals (resp.status_code, 200)
            #
            # fill the form with reservation data and save it
            #
            instance = resp.context[-1]['form'].instance
            desc = 'Testing club reservation %s' % str(instance.vacancy.id)
            resp = self.cli.post (view_url,
                                  {'created_on': instance.created_on,
                                   'for_date': instance.for_date,
                                   'type': instance.type,
                                   'description': desc,
                                   'user': instance.user.id,
                                   'vacancy': instance.vacancy.id},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            form = resp.context[-1]['form']
            self.assertEquals (len (form.errors.keys ( )), 0, form.errors)
            try:
                r = Reservation.objects.get_by_date (for_date).get (vacancy=v)
                self.assertIsInstance (r, Reservation)
                self.assertEquals (r.for_date, for_date)
                self.assertEquals (r.type, 'C')
                self.assertEquals (r.description, desc)
                self.assertEquals (r.user, self.club.user)
                self.assertEquals (r.vacancy, v)
                
            except ObjectDoesNotExist:
                self.assertTrue (False,
                                 'The view did not save the reservation correctly.-')
                