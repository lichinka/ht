from random import randint
from datetime import date, datetime, timedelta

from django.test import TestCase
from django.db.utils import IntegrityError
from django.test.client import Client
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models.deletion import ProtectedError
from django.contrib.auth.models import User
from django.db.models.aggregates import Count

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
        p.first_name = 'Andre'
        p.last_name = 'Agassi'
        p.save ( )
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
        for i in range (3, randint (3, 7)):
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
        #
        # add some player reservations
        #
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( ))
        for i in range (50, randint (55, 60)):
            v = all_vacancies[i]
            for_date = date.today ( ) + timedelta (days=i%7)
            try:
                Reservation.objects.create (created_on=datetime.now ( ),
                                            for_date=for_date,
                                            type='P',
                                            description="Player's testing reservation",
                                            user=self.player.user,
                                            vacancy=v,
                                            repeat_series=None)
            except IntegrityError:
                pass
            
        #
        # randomly select some vacancies and reserve them
        # with and without weekly repetition (for the club only)
        #
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( ))
        for i in range (0, randint (5, 10)):
            v = all_vacancies[i]
            for_date = date.today ( ) + timedelta (days=i%7)
            if i%4 == 0:
                #
                # create a reservation with weekly repetition
                #
                until_date = for_date + timedelta (days=randint (3, 60))
                repeat_dates = [for_date]
                while until_date > repeat_dates[-1]:
                    next_date = repeat_dates[-1] + timedelta (days=7)
                    repeat_dates.append (next_date)
                if repeat_dates[-1] > until_date:
                    repeat_dates.pop ( )
                for d in repeat_dates:
                    try:
                        Reservation.objects.create (created_on=datetime.now ( ),
                                                    for_date=d,
                                                    type='C',
                                                    description="Testing reservation",
                                                    user=self.club.user,
                                                    vacancy=v,
                                                    repeat_series=i)
                    except IntegrityError:
                        pass
            else:
                #
                # reservation without repetition
                #
                try:
                    Reservation.objects.create (created_on=datetime.now ( ),
                                                for_date=for_date,
                                                type='C',
                                                description="Testing reservation",
                                                user=self.club.user,
                                                vacancy=v,
                                                repeat_series=None)
                except IntegrityError:
                    pass
    
    def test_cancel (self):
        """
        Checks the behavior of reservations.views.cancel.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        """
        #
        # physically delete only the reservations owned by the user
        #
        reservations = Reservation.objects.exclude (user=self.club.user) \
                                          .filter (repeat_series__isnull=True)
        reservation_count = reservations.aggregate (Count ('id'))['id__count']
        self.assertNotEquals (reservation_count, 0)
        
        r = reservations[randint (0, reservation_count - 1)]
        self.assertIsInstance (r, Reservation)
        
        view_url = reverse ('reservations.views.cancel',
                            args=[r.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 404)
        self.assertEquals (reservations.aggregate (Count ('id'))['id__count'],
                           reservation_count)
        """
        #
        # cancel strictly one reservation when it is not part of a
        # repetition series
        #
        reservations = Reservation.objects.filter (user=self.club.user,
                                                   repeat_series__isnull=True)
        reservation_count = reservations.aggregate (Count ('id'))['id__count']
        self.assertNotEquals (reservation_count, 0)
        
        r = reservations[randint (0, reservation_count - 1)]
        self.assertIsInstance (r, Reservation)
        
        view_url = reverse ('reservations.views.cancel',
                            args=[r.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'reservations/club_view.html')
        self.assertEquals (reservations.aggregate (Count ('id'))['id__count'],
                           reservation_count - 1)
        #
        # cancel all the reservations in a repetition series
        #
        reservations = Reservation.objects.filter (user=self.club.user,
                                                   repeat_series__isnull=False)
        reservation_count = reservations.aggregate (Count ('id'))['id__count']
        self.assertNotEquals (reservation_count, 0)
        
        r = reservations[randint (0, reservation_count - 1)]
        self.assertIsInstance (r, Reservation)
        
        series_count = Reservation.objects.filter (user=self.club.user,
                                                   repeat_series=r.repeat_series)
        series_count = series_count.aggregate (Count ('id'))['id__count']
        self.assertNotEquals (series_count, 0)
        
        view_url = reverse ('reservations.views.cancel',
                            args=[r.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'reservations/club_view.html')
        self.assertEquals (reservations.aggregate (Count ('id'))['id__count'],
                           reservation_count - series_count)
        
            
    def test_player_edit (self):
        """
        Checks the behavior of reservations.views.player_edit.-
        """
        #
        # log the player in
        #
        self.cli.login (username=self.T_PLAYER['username'],
                        password=self.T_PLAYER['password'])
        #
        # randomly select some free vacancies and reserve them
        #
        existing_reservations = Reservation.objects.all ( ).values ('vacancy__id')
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( )) \
                                       .exclude (id__in=existing_reservations)
        for i in range (0, randint (0, 10)):
            v = all_vacancies[i]
            for_date = date.today ( ) + timedelta (days=i%4)
            view_url = reverse ('reservations.views.player_edit',
                                args=[v.id, for_date.toordinal ( )])
            reservation_count = Reservation.objects.all ( ).aggregate (Count ('id'))
            #
            # correctly display the reservation form
            #
            resp = self.cli.get (view_url)
            self.assertEquals (resp.status_code, 200)
            #
            # fill the form with reservation data and save it
            #
            form = resp.context[-1]['form']
            resp = self.cli.post (view_url,
                                  {'created_on': form.instance.created_on,
                                   'for_date': form.instance.for_date,
                                   'type': form.instance.type,
                                   'user': form.instance.user.id,
                                   'vacancy': form.instance.vacancy.id,
                                   'repeat': form.initial['repeat'],
                                   'repeat_until': form.initial['repeat_until']},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            if 'form' in resp.context[-1]:
                form = resp.context[-1]['form']
                self.assertEquals (len (form.errors.keys ( )), 0, form.errors)
            self.assertEquals (Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'],
                               reservation_count['id__count'] + 1)
            try:
                r = Reservation.objects.get_by_date (for_date).get (vacancy=v)
                self.assertIsInstance (r, Reservation)
                self.assertEquals (r.for_date, for_date)
                self.assertEquals (r.type, 'P')
                self.assertEquals (r.description, u'%s, %s' % (self.player.user.last_name,
                                                               self.player.user.first_name))
                self.assertEquals (r.user, self.player.user)
                self.assertEquals (r.vacancy, v)
                self.assertIsNone (r.repeat_series)
                
            except ObjectDoesNotExist:
                self.assertTrue (False,
                                 'The view did not save the reservation correctly.-')
        #
        # cannot edit an existing reservation this player doesn't own
        #
        existing_reservations = Reservation.objects.filter (user=self.club.user) \
                                                   .values ('vacancy__id')
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( )) \
                                       .filter (id__in=existing_reservations)
        for i in range (0, randint (0, 5)):
            v = all_vacancies[i]
            for_date = Reservation.objects.filter (vacancy=v)
            for_date = for_date[0].for_date
            view_url = reverse ('reservations.views.player_edit',
                                args=[v.id, for_date.toordinal ( )])
            #
            # 404 because the logged in user does not own the reservation
            #
            resp = self.cli.get (view_url)
            self.assertEquals (resp.status_code, 404)
        #
        # change reservations this player owns
        #
        existing_reservations = Reservation.objects.filter (user=self.player.user) \
                                                   .values ('vacancy__id')
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( )) \
                                       .filter (id__in=existing_reservations)
        for i in range (0, randint (0, 5)):
            v = all_vacancies[i]
            for_date = Reservation.objects.filter (vacancy=v)
            for_date = for_date[0].for_date
            view_url = reverse ('reservations.views.player_edit',
                                args=[v.id, for_date.toordinal ( )])
            reservation_count = Reservation.objects.all ( ).aggregate (Count ('id'))
            #
            # correctly display the reservation form
            #
            resp = self.cli.get (view_url)
            self.assertEquals (resp.status_code, 200)
            #
            # fill the form with different data and save it
            #
            form = resp.context[-1]['form']
            resp = self.cli.post (view_url,
                                  {'created_on': form.instance.created_on,
                                   'for_date': form.instance.for_date,
                                   'type': form.instance.type,
                                   'user': form.instance.user.id,
                                   'vacancy': form.instance.vacancy.id,
                                   'repeat': form.initial['repeat'],
                                   'repeat_until': form.initial['repeat_until']},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            if 'form' in resp.context[-1]:
                form = resp.context[-1]['form']
                self.assertEquals (len (form.errors.keys ( )), 0, form.errors)
            self.assertEquals (Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'],
                               reservation_count['id__count'])
            try:
                r = Reservation.objects.get_by_date (for_date).get (vacancy=v)
                self.assertIsInstance (r, Reservation)
                self.assertEquals (r.for_date, for_date)
                self.assertEquals (r.type, 'P')
                self.assertEquals (r.description, u'%s, %s' % (self.player.user.last_name,
                                                               self.player.user.first_name))
                self.assertEquals (r.user, self.player.user)
                self.assertEquals (r.vacancy, v)
                self.assertIsNone (r.repeat_series)
                
            except ObjectDoesNotExist:
                self.assertTrue (False,
                                 'The view did not save the reservation correctly.-')
        
        
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
        existing_reservations = Reservation.objects.all ( ).values ('vacancy__id')
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( )) \
                                       .exclude (id__in=existing_reservations)
        vacancy_count = all_vacancies.aggregate (Count ('id'))['id__count']
        for i in range (0, randint (0, vacancy_count%10)):
            v = all_vacancies[i]
            for_date = date.today ( ) + timedelta (days=i%7)
            view_url = reverse ('reservations.views.club_edit',
                                args=[v.id, for_date.toordinal ( )])
            reservation_count = Reservation.objects.all ( ).aggregate (Count ('id'))
            #
            # correctly display the reservation form
            #
            resp = self.cli.get (view_url)
            self.assertEquals (resp.status_code, 200)
            #
            # fill the form with reservation data and save it
            #
            form = resp.context[-1]['form']
            desc = 'Testing club reservation %s' % str(form.instance.vacancy.id)
            resp = self.cli.post (view_url,
                                  {'created_on': form.instance.created_on,
                                   'for_date': form.instance.for_date,
                                   'type': form.instance.type,
                                   'description': desc,
                                   'user': form.instance.user.id,
                                   'vacancy': form.instance.vacancy.id,
                                   'repeat': form.initial['repeat'],
                                   'repeat_until': form.initial['repeat_until']},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            form = resp.context[-1]['form']
            self.assertEquals (len (form.errors.keys ( )), 0, form.errors)
            self.assertEquals (Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'],
                               reservation_count['id__count'] + 1)
            try:
                r = Reservation.objects.get_by_date (for_date).get (vacancy=v)
                self.assertIsInstance (r, Reservation)
                self.assertEquals (r.for_date, for_date)
                self.assertEquals (r.type, 'C')
                self.assertEquals (r.description, desc)
                self.assertEquals (r.user, self.club.user)
                self.assertEquals (r.vacancy, v)
                self.assertIsNone (r.repeat_series)
                
            except ObjectDoesNotExist:
                self.assertTrue (False,
                                 'The view did not save the reservation correctly.-')
        #
        # randomly select some vacancies and reserve with weekly repetition
        #
        existing_reservations = Reservation.objects.all ( ).values ('vacancy__id')
        all_vacancies = Vacancy.objects.get_all (self.courts.values ( )) \
                                       .exclude (id__in=existing_reservations)
        vacancy_count = all_vacancies.aggregate (Count ('id'))['id__count']
        for i in range (0, randint (0, vacancy_count%10)):
            v = all_vacancies[i]
            for_date = date.today ( ) + timedelta (days=i%7)
            view_url = reverse ('reservations.views.club_edit',
                                args=[v.id, for_date.toordinal ( )])
            reservation_count = Reservation.objects.all ( ).aggregate (Count ('id'))
            #
            # correctly display the reservation form
            #
            resp = self.cli.get (view_url)
            self.assertEquals (resp.status_code, 200)
            #
            # fill the form with invalid data and try to save it
            #
            form = resp.context[-1]['form']
            desc = 'Testing club invalid reservation %s' % str(form.instance.vacancy.id)
            resp = self.cli.post (view_url,
                                  {'created_on': form.instance.created_on,
                                   'for_date': form.instance.for_date,
                                   'type': form.instance.type,
                                   'description': desc,
                                   'user': form.instance.user.id,
                                   'vacancy': form.instance.vacancy.id,
                                   'repeat': True,
                                   'repeat_until': form.instance.for_date - timedelta (days=2)},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            form = resp.context[-1]['form']
            self.assertTrue (len (form.errors.keys ( )) > 0)
            self.assertEquals (Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'],
                               reservation_count['id__count'])
            #
            # fill the form with reservation (repeat) data and save it
            #
            form = resp.context[-1]['form']
            until_date = form.instance.for_date + timedelta (days=randint (3, 60))
            repeat_dates = [form.instance.for_date]
            while until_date > repeat_dates[-1]:
                next_date = repeat_dates[-1] + timedelta (days=7)
                repeat_dates.append (next_date)
            if repeat_dates[-1] > until_date:
                repeat_dates.pop ( )
            desc = 'Testing club reservation series %s' % str(form.instance.vacancy.id)
            resp = self.cli.post (view_url,
                                  {'created_on': form.instance.created_on,
                                   'for_date': form.instance.for_date,
                                   'type': form.instance.type,
                                   'description': desc,
                                   'user': form.instance.user.id,
                                   'vacancy': form.instance.vacancy.id,
                                   'repeat': True,
                                   'repeat_until': until_date},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            form = resp.context[-1]['form']
            self.assertEquals (len (form.errors.keys ( )), 0, form.errors)
            self.assertEquals (Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'],
                               reservation_count['id__count'] + len (repeat_dates))
            #
            # retrieve the repetition series identifier from the first
            # reservation in the series
            #
            try:
                r = Reservation.objects.get_by_date (for_date).get (vacancy=v)
                self.assertIsNotNone (r.repeat_series)
                rep_series = r.repeat_series
            except ObjectDoesNotExist:
                self.assertTrue (False,
                                 'The view did not save the reservation series correctly.-')
            #
            # check that all reservations in the repetition series match
            #
            for d in repeat_dates:
                try:
                    r = Reservation.objects.get_by_date (d).get (vacancy=v)
                    self.assertIsInstance (r, Reservation)
                    self.assertEquals (r.for_date, d)
                    self.assertEquals (r.type, 'C')
                    self.assertEquals (r.description, desc)
                    self.assertEquals (r.user, self.club.user)
                    self.assertEquals (r.vacancy, v)
                    self.assertEquals (r.repeat_series, rep_series)
                except ObjectDoesNotExist:
                    self.assertTrue (False,
                                     'The view did not save the reservation series correctly.-')
                
