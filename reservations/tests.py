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
from ht_utils.tests import BaseViewTestCase
from accounts.models import UserProfile
from locations.models import City
from reservations.models import Reservation
from ht_utils import pick_random_element




class ClubEditTest (BaseViewTestCase):
    """
    All test cases for this view.-
    """
    def setUp (self):
        BaseViewTestCase.setUp (self)
        #
        # view internal path
        #
        self.view_path = 'reservations.views.club_edit'
        self.template_name = 'reservations/club_edit.html'
        
        
    def test_only_object_owner_has_access (self):
        #
        # log the player in
        #
        self.cli.login (username=self.T_PLAYER['username'], 
                        password=self.T_PLAYER['password'])
        cs = CourtSetup.objects.get_active (self.club)
        v = None
        while v is None:
            v = Vacancy.objects.get_free (cs,
                                          date.today ( ),
                                          Vacancy.HOURS[randint(0, 15)][0])
            v = v[0] if v else None
        view_url = reverse (self.view_path,
                            args=[v.id, date.today ( ).toordinal ( )])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 404)
        
        
    def test_existance_and_correct_template (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        cs = CourtSetup.objects.get_active (self.club)
        v = None
        while v is None:
            v = Vacancy.objects.get_free (cs,
                                          date.today ( ),
                                          Vacancy.HOURS[randint(0, 15)][0])
            v = v[0] if v else None
        view_url = reverse (self.view_path,
                            args=[v.id, date.today ( ).toordinal ( )])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, self.template_name)
        
        
    def test_description_should_not_be_empty_if_weekly_repeat_is_on (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # randomly select some vacancies and reserve with weekly repetition
        #
        cs = CourtSetup.objects.get_active (self.club)
        for i in range (0, randint (3, 10)):
            for_date = date.today ( ) + timedelta (days=i%7)
            hour = Vacancy.HOURS[i%15][0]
            is_free = Vacancy.objects.get_free (cs, for_date, hour)
            if is_free:
                v = is_free[0]
                break
        view_url = reverse ('reservations.views.club_edit',
                            args=[v.id, for_date.toordinal ( )])
        reservation_count = Reservation.objects.all ( ).aggregate (Count ('id'))
        #
        # correctly display the reservation form
        #
        resp = self.cli.get (view_url)
        self.assertEquals (resp.status_code, 200)
        #
        # fill the form without description and try to save it
        #
        form = resp.context[-1]['form']
        resp = self.cli.post (view_url,
                              {'created_on': form.instance.created_on,
                               'for_date': form.instance.for_date,
                               'type': form.instance.type,
                               'description': '     ',
                               'user': form.instance.user.id,
                               'vacancy': form.instance.vacancy.id,
                               'repeat': True,
                               'repeat_until': form.instance.for_date + timedelta (days=2)},
                              follow=True)
        self.assertEquals (resp.status_code, 200)
        form = resp.context[-1]['form']
        self.assertTrue (len (form.errors.keys ( )) > 0)
        self.assertEquals (Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'],
                           reservation_count['id__count'])
   
    
    def test_single_term_reservation_by_club (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # randomly select some free vacancies and reserve them by club
        #
        cs = CourtSetup.objects.get_active (self.club)
        for i in range (0, randint (3, 10)):
            for_date = date.today ( ) + timedelta (days=i%7)
            hour = Vacancy.HOURS[i%15][0]
            is_free = Vacancy.objects.get_free (cs, for_date, hour)
            if is_free:
                v = is_free[0]
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
                    r = Reservation.objects.by_date (v.court.court_setup, for_date) \
                                           .get (vacancy=v)
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
                    
    
    def test_invalid_reservation_by_club_with_weekly_repetition (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # randomly select some vacancies and try to reserve
        # them with weekly repetition
        #
        cs = CourtSetup.objects.get_active (self.club)
        for i in range (0, randint (3, 10)):
            for_date = date.today ( ) + timedelta (days=i%7)
            hour = Vacancy.HOURS[i%15][0]
            is_free = Vacancy.objects.get_free (cs, for_date, hour)
            if is_free:
                v = is_free[0]
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
                
                    
    def test_term_reservation_by_club_with_weekly_repetition (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # randomly select some vacancies and reserve them with weekly repetition
        #
        cs = CourtSetup.objects.get_active (self.club)
        for i in range (0, randint (3, 10)):
            for_date = date.today ( ) + timedelta (days=i%7)
            hour = Vacancy.HOURS[i%15][0]
            is_free = Vacancy.objects.get_free (cs, for_date, hour)
            if is_free:
                v = is_free[0]
                view_url = reverse ('reservations.views.club_edit',
                                    args=[v.id, for_date.toordinal ( )])
                reservation_count = Reservation.objects.all ( ).aggregate (Count ('id'))
                #
                # correctly display the reservation form
                #
                resp = self.cli.get (view_url)
                self.assertEquals (resp.status_code, 200)
                #
                # fill the form with reservation (repeat) data and save it
                #
                form = resp.context[-1]['form']
                until_date = form.instance.for_date + timedelta (days=randint (13, 60))
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
                    r = Reservation.objects.by_date (v.court.court_setup, for_date) \
                                           .get (vacancy=v)
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
                        r = Reservation.objects.by_date (v.court.court_setup, d) \
                                               .get (vacancy=v)
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


                    
class TransferOrDeleteTest (BaseViewTestCase):
    """
    All the test cases for this view.-
    """
    def setUp (self):
        BaseViewTestCase.setUp (self)
        #
        # get a court setup WITH reservations
        #
        for cs in self.cs_list:
            r = Reservation.objects.by_court_setup (cs)
            if r:
                self.booked_cs = CourtSetup.objects.get (pk=cs.id)
                break
        
        
    def test_only_object_owner_has_access (self):
        #
        # log the player in
        #
        self.cli.login (username=self.T_PLAYER['username'], 
                        password=self.T_PLAYER['password'])
        self.assertIsInstance (self.booked_cs, CourtSetup)
        view_url = reverse ('reservations.views.transfer_or_delete',
                            args=[self.booked_cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 404)
        
        
    def test_existance_and_correct_template (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        self.assertIsInstance (self.booked_cs, CourtSetup)
        view_url = reverse ('reservations.views.transfer_or_delete',
                            args=[self.booked_cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'reservations/transfer_or_delete.html')

        
    def test_transfer_to_is_required_only_for_transfer_actions (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        self.assertIsInstance (self.booked_cs, CourtSetup)
        view_url = reverse ('reservations.views.transfer_or_delete',
                            args=[self.booked_cs.id])
        #
        # transfer action options
        #
        for choice in [1]:
            resp = self.cli.post (view_url, 
                                  {'user_choice': choice,
                                   'transfer_to': ''},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            form = resp.context[-1]['form']
            self.assertNotEquals (len (form.errors), 0)
        #
        # not-transfer action options
        #   
        for choice in [2, 3]:
            resp = self.cli.post (view_url, 
                                  {'user_choice': choice,
                                   'transfer_to': ''},
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            form = resp.context[-1]['form']
            self.assertEquals (len (form.errors), 0)


class ReservationTest (BaseViewTestCase):
    """
    All the test cases for the Reservation model.-
    """
    def test_manager_book_weekly (self):
        """
        Checks correct booking of weekly repeating terms.-
        """
        #
        # no reservations are booked if invalid dates are given
        #
        from_date = date.today ( ) + timedelta (days=randint (0, 10))
        until_date = from_date - timedelta (days=randint (5, 15))
        res_count = Reservation.objects.all ( ) \
                                       .aggregate (Count ('id'))
        # number of days between the two dates
        booking_count = abs ((until_date - from_date).days)
        # number of weekly reservations (i.e. every 7 days) 
        # starting (and including) 'from_date'
        booking_count += 7 - (booking_count % 7)
        booking_count /= 7
        booked = Reservation.objects.book_weekly (from_date, until_date)
        self.assertEquals (len(booked), 0)
        self.assertEquals (res_count,
                           Reservation.objects.all ( ).aggregate (Count ('id')))
        #
        # not all reservations are booked if any term is not free
        #
        res = pick_random_element (self.res_list)
        from_date = res.for_date
        v = res.vacancy
        until_date = from_date + timedelta (days=randint (5, 15))
        res_count = Reservation.objects.all ( ) \
                                       .aggregate (Count ('id'))
        # number of days between the two dates
        booking_count = (until_date - from_date).days
        self.assertFalse (booking_count < 0)
        # number of weekly reservations (i.e. every 7 days) 
        # starting (and including) 'from_date'
        booking_count += 7 - (booking_count % 7)
        booking_count /= 7
        booked = Reservation.objects.book_weekly (from_date, 
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  description="Weekly reservations",
                                                  commit=True)
        self.assertTrue (len(booked) < booking_count)
        self.assertEquals (res_count['id__count'] + len(booked),
                           Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'])
        #
        # correct booking in case of valid dates and free terms
        #
        cs = CourtSetup.objects.get_active (self.club)
        v = None
        while v is None:
            from_date = date.today ( ) + timedelta (days=randint (0, 10))
            v = Vacancy.objects.get_free (cs, from_date, Vacancy.HOURS[randint (0, 15)][0])
            v = v[0] if v else None
                
        until_date = from_date + timedelta (days=randint (5, 15))
        res_count = Reservation.objects.all ( ) \
                                       .aggregate (Count ('id'))
        # number of days between the two dates
        booking_count = (until_date - from_date).days
        self.assertFalse (booking_count < 0)
        # number of weekly reservations (i.e. every 7 days) 
        # starting (and including) 'from_date'
        booking_count += 7 - (booking_count % 7)
        booking_count /= 7
        #
        # if no commit, the record count on the DB should be unaltered
        #
        booked = Reservation.objects.book_weekly (from_date, 
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  description="Weekly reservations",
                                                  commit=False)
        self.assertEquals (len(booked), booking_count)
        self.assertEquals (res_count['id__count'],
                           Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'])
        #
        # if committing, the record count on the DB should grow
        #
        desc = "Weekly reservations"
        booked = Reservation.objects.book_weekly (from_date, 
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  description=desc,
                                                  commit=True)
        self.assertEquals (len(booked), booking_count)
        self.assertEquals (res_count['id__count'] + booking_count,
                           Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'])
        #
        # the number of saved reservations with the
        # new series identifier should be correct
        # 
        res_count = Reservation.objects.filter (repeat_series=booked[0].repeat_series) \
                                       .aggregate (Count ('id'))['id__count']
        self.assertEquals (res_count, len(booked))
        #
        # data correctness for all saved reservations
        #
        for idx in range (0, len(booked)):
            new_booking = Reservation.objects.get (pk=booked[idx].id)
            for_date = from_date + timedelta (days=idx*7)
            
            self.assertEquals (new_booking.for_date, for_date)
            self.assertEquals (new_booking.vacancy, v)
            self.assertEquals (new_booking.user, self.club.user)
            self.assertEquals (new_booking.type, 'C')
            self.assertEquals (new_booking.description, desc)
            self.assertEquals (new_booking.repeat_series, booked[0].repeat_series)
            
    
    def test_manager_get_next_repeat_series (self):
        """
        The retrieved identifier should be valid (i.e. not existing in DB).-
        """
        next_id = Reservation.objects.get_next_repeat_series ( )
        res_count = Reservation.objects.filter (repeat_series=next_id) \
                                       .aggregate (Count ('id'))
        self.assertEquals (res_count['id__count'], 0)
    
    
    def test_manager_book (self):
        """
        Checks correct booking of free vacancy terms.-
        """
        #
        # cannot book a taken term
        #
        r = pick_random_element (self.res_list)
        taken_term = r.vacancy
        for_date = r.for_date
        description = "Testing the book (...) method"
        repeat_series = None
        booking = Reservation.objects.book (for_date=for_date, 
                                            vacancy=taken_term, 
                                            user=self.player.user, 
                                            description=description,
                                            repeat_series=repeat_series)
        self.assertIsNone (booking)
        #
        # the court should be available
        #
        cs = CourtSetup.objects.get_active (self.club)
        court_off = Court.objects.filter (court_setup=cs) \
                                 .filter (is_available=False)
        if court_off:
            court_off = court_off[0]
            for_date = date.today ( ) + timedelta(days=randint (0, 5))
            hour = Vacancy.HOURS[randint(0, 15)][0]
            term = Vacancy.objects.get (court=court_off,
                                        day_of_week=for_date.isoweekday ( ),
                                        available_from=hour)
            description = "Testing the book (...) method"
            repeat_series = None
            booking = Reservation.objects.book (for_date=for_date, 
                                                vacancy=term, 
                                                user=self.player.user, 
                                                description=description,
                                                repeat_series=repeat_series)
            self.assertIsNone (booking)
        #
        # reservations should be correctly created
        # and commit works as expected
        #
        cs = CourtSetup.objects.get_active (self.club)
        for court in Court.objects.get_available (cs).iterator ( ):
            for_date = date.today ( ) + timedelta(days=randint (0, 5))
            hour = Vacancy.HOURS[randint(0, 15)][0]
            term = Vacancy.objects.get (court=court,
                                        day_of_week=for_date.isoweekday ( ),
                                        available_from=hour)
            description = "Testing the book (...) method"
            repeat_series = court.number * 10
            commit = not (court.number%2 == 0)
            
            free_terms = [t['id'] for t in Vacancy.objects.get_free (cs, for_date, hour).values ('id')]
            booking = Reservation.objects.book (for_date=for_date, 
                                                vacancy=term, 
                                                user=self.player.user if court.number%2 == 0 else self.club.user, 
                                                description=description,
                                                repeat_series=repeat_series,
                                                commit=commit)
            if term.id in free_terms:
                #
                # the term was free, reservation should be ok; it
                # should also appear in the DB if commit was True
                #
                try:
                    new_booking = Reservation.objects.get (pk=booking.id)
                    #
                    # reservation appears in the DB: commit should be True
                    #
                    self.assertTrue (commit)
                except ObjectDoesNotExist:
                    #
                    # reservation has not been saved: commit should be False
                    #
                    new_booking = booking
                    self.assertFalse (commit)
                self.assertEquals (new_booking.for_date, for_date)
                self.assertEquals (new_booking.vacancy, term)
                if court.number%2 == 0:
                    self.assertEquals (new_booking.user, self.player.user)
                    self.assertEquals (new_booking.type, 'P')
                else:
                    self.assertEquals (new_booking.user, self.club.user)
                    self.assertEquals (new_booking.type, 'C')
                self.assertEquals (new_booking.description, description)
                self.assertEquals (new_booking.repeat_series, repeat_series)
            else:
                #
                # the term was taken, booking should fail
                #
                self.assertIsNone (booking)
            
        
    def test_manager_copy_individual_reservations_to_court_setup (self):
        """
        Correctly copy reservations to another court setup.-
        """
        source_cs = self.res_list[0].vacancy.court.court_setup
        #
        # get a court setup capable of accommodating all
        # reservations of the source court setup
        #
        for cs in self.cs_list:
            target_cs = CourtSetup.objects.get (pk=cs.id)
            if source_cs != target_cs:
                for r in Reservation.objects.by_court_setup (cs):
                    free_terms = Vacancy.objects.get_free (cs, 
                                                           r.for_date, 
                                                           r.vacancy.available_from)
                    free_terms = free_terms.aggregate (Count ('id'))
                    if int(free_terms['id__count']) == 0:
                        target_cs = None
                #
                # did we find a target court setup?
                #
                if target_cs is not None:
                    break
        #
        # make sure the target court setup is valid
        #            
        self.assertIsNotNone (target_cs)
        self.assertIsInstance (target_cs, CourtSetup)
        self.assertNotEquals (source_cs, target_cs)
        #
        # check that all reservations are correctly copied, without committing to DB
        # 
        source_cs_count = Reservation.objects.by_court_setup (source_cs) \
                                             .aggregate (Count ('id'))['id__count']
        target_cs_count = Reservation.objects.by_court_setup (target_cs) \
                                             .aggregate (Count ('id'))['id__count']
        copied = Reservation.objects.copy_to_court_setup (target_cs, self.res_list, commit=False)
        self.assertEquals (len (copied), len (self.res_list)) 
        self.assertEquals (Reservation.objects.by_court_setup (source_cs).aggregate (Count('id'))['id__count'],
                           source_cs_count)
        self.assertEquals (Reservation.objects.by_court_setup (target_cs).aggregate (Count('id'))['id__count'],
                           target_cs_count)
        #
        # check that all reservations are correctly copied, but saving to DB
        # 
        source_cs_count = Reservation.objects.by_court_setup (source_cs) \
                                             .aggregate (Count ('id'))['id__count']
        target_cs_count = Reservation.objects.by_court_setup (target_cs) \
                                             .aggregate (Count ('id'))['id__count']
        copied = Reservation.objects.copy_to_court_setup (target_cs, self.res_list, commit=True)
        self.assertEquals (len (copied), len (self.res_list))
        self.assertEquals (Reservation.objects.by_court_setup (source_cs).aggregate (Count('id'))['id__count'],
                           source_cs_count)
        self.assertEquals (Reservation.objects.by_court_setup (target_cs).aggregate (Count('id'))['id__count'],
                           len(self.res_list) + target_cs_count)
        #
        # check that all copied reservations are correct
        #
        for src_r in self.res_list:
            tgt_r = Reservation.objects.by_date (target_cs, src_r.for_date) \
                                       .filter (vacancy__available_from = src_r.vacancy.available_from)
            tgt_r = tgt_r[0]
            self.assertIsNotNone (tgt_r)
            self.assertIsInstance (tgt_r, Reservation)
            self.assertEquals (src_r.for_date, tgt_r.for_date)
            self.assertEquals (src_r.vacancy.day_of_week, tgt_r.vacancy.day_of_week)
            self.assertEquals (src_r.vacancy.available_from, tgt_r.vacancy.available_from)
            self.assertEquals (src_r.vacancy.available_to, tgt_r.vacancy.available_to)
            self.assertEquals (target_cs, tgt_r.vacancy.court.court_setup)
            self.assertEquals (src_r.user, tgt_r.user)
            self.assertEquals (src_r.description, tgt_r.description)
            self.assertEquals (src_r.repeat_series, tgt_r.repeat_series)

        
    def test_manager_copy_repeating_reservations_to_court_setup (self):
        """
        Correctly copy reservations to another court setup.-
        """
        #
        # add a repeating reservation, making sure we can accommodate it
        #
        source_cs = CourtSetup.objects.get_active (self.club)
        from_date = date.today ( ) + timedelta (days=randint (0, 10))
        until_date = from_date + timedelta (days=randint (8, 25))
        vacancy = None
        while vacancy is None:
            vacancy = Vacancy.objects.get_free (source_cs, 
                                                from_date, 
                                                Vacancy.HOURS[randint(0, 15)][0])
            vacancy = vacancy[0] if vacancy else None
            
        booked = Reservation.objects.book_weekly (from_date, until_date, commit=False,
                                                  vacancy=vacancy,
                                                  description="Testing description",
                                                  user=self.club.user)
        self.assertEquals (len(booked), 
                           Reservation.objects.get_weekly_reservation_count (from_date,
                                                                             until_date))
        booked = Reservation.objects.book_weekly (from_date, until_date, commit=True,
                                                  vacancy=vacancy,
                                                  description="Testing description",
                                                  user=self.club.user)
        self.assertEquals (len(booked), 
                           Reservation.objects.get_weekly_reservation_count (from_date,
                                                                             until_date))
        #
        # try to copy the repeating reservations to another court setup
        #
        target_cs = source_cs
        while target_cs == source_cs:
            target_cs = pick_random_element (self.cs_list)
        
        booked_copy = Reservation.objects.copy_to_court_setup (target_cs, booked, commit=False)
        self.assertTrue (len (booked_copy) <= len (booked))
        #
        # check the correctness of the copied and (possibly)
        # not copied reservations
        #
        repeat_id = booked_copy[0].repeat_series
        for tgt_r in booked_copy:
            for src_r in booked:
                if src_r.for_date == tgt_r.for_date:
                    self.assertEquals (src_r.for_date, tgt_r.for_date)
                    self.assertEquals (src_r.vacancy.day_of_week, tgt_r.vacancy.day_of_week)
                    self.assertEquals (src_r.vacancy.available_from, tgt_r.vacancy.available_from)
                    self.assertEquals (src_r.vacancy.available_to, tgt_r.vacancy.available_to)
                    self.assertEquals (target_cs, tgt_r.vacancy.court.court_setup)
                    self.assertEquals (src_r.user, tgt_r.user)
                    self.assertEquals (src_r.description, tgt_r.description)
                    self.assertEquals (tgt_r.repeat_series, repeat_id)
                    booked.pop (booked.index (src_r))
        #
        # check that not copied reservations have their target
        # terms actually taken
        #
        for src_r in booked:
            tgt_v = Vacancy.objects.get_free (target_cs,
                                              src_r.for_date,
                                              src_r.vacancy.available_from)
            tgt_v = tgt_v.aggregate (Count ('id'))
            self.assertTrue (tgt_v['id__count'], 0)
   
    
    def test_default_type_is_player (self):
        """
        The default reservation type should be 'by player'.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        c = Court.objects.get_available (cs)
        for i in range (0, randint (1, 7)):
            v = Vacancy.objects.get_all ([c[0]], [Vacancy.DAYS[i][0]])
            try:
                r = Reservation.objects.create (for_date=date.today ( ),
                                                description="Test reservation",
                                                user=self.player.user,
                                                vacancy=v[i])
                r.save ( )
                r = Reservation.objects.get (pk=r.id)
                self.assertEquals (r.type, 'P')
            except IntegrityError:
                pass
            
                
    def test_cannot_delete_reserved_vacancy (self):
        """
        A reservation cannot be deleted indirectly by deleting the 
        referenced vacancy.-
        """
        #
        # try to indirectly delete some reservations via their
        # referenced vacancies (should throw exception)
        #
        v_ids = Reservation.objects.filter (user=self.player.user) \
                                   .values ('vacancy__id')
        for v in v_ids:
            try:
                Vacancy.objects.get (pk=v['vacancy__id']).delete ( )
                self.assertTrue (False)
            except ProtectedError:
                self.assertTrue (True)
                
                
    def test_manager_by_date (self):
        """
        Checks that the number of reservations returned
        by this method is correct.-
        """
        cs = pick_random_element (self.cs_list)
        court_count = Court.objects.get_count (cs)
        hour_count = len (Vacancy.HOURS) - 1
        term_count = court_count * hour_count
        for_date = date.today ( )
        booked = Reservation.objects.by_date (cs, for_date) \
                                    .values ('vacancy__id')
        free = Vacancy.objects.filter (court__court_setup=cs) \
                              .filter (day_of_week=for_date.isoweekday ( )) \
                              .exclude (id__in=booked) \
                              .values ('id')
        self.assertEquals (term_count, len(booked) + len(free))
        
            
    def test_manager_from_date (self):
        """
        Checks that the number of reservations returned
        by this method is correct.-
        """
        cs = pick_random_element (self.cs_list)
        court_count = Court.objects.get_count (cs)
        from_date = date.today ( )
        booked_dates = Reservation.objects.from_date (cs, from_date) \
                                          .values ('for_date').distinct ( )
        hour_count = len (Vacancy.HOURS) - 1
        term_count = court_count * len(booked_dates) * hour_count
        booked = Reservation.objects.from_date (cs, from_date) \
                                    .values ('vacancy__id')
        free_count = 0
        for d in booked_dates:
            free = Vacancy.objects.filter (court__court_setup=cs) \
                                  .filter (day_of_week=d['for_date'].isoweekday ( )) \
                                  .exclude (id__in=booked) \
                                  .values ('id')
            free_count += len (free)
        self.assertEquals (term_count, len(booked) + free_count)
        
        
    
                
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
                r = Reservation.objects.by_date (v.court.court_setup, for_date) \
                                       .get (vacancy=v)
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
                r = Reservation.objects.by_date (v.court.court_setup, for_date) \
                                       .get (vacancy=v)
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

    