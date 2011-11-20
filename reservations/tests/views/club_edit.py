from random import randint
from datetime import date, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Count

from clubs.models import CourtSetup, Vacancy
from ht_utils.tests import BaseViewTestCase
from reservations.models import Reservation



class ClubEditTest (BaseViewTestCase):
    """
    All test cases for this view.-
    """
    def setUp (self):
        BaseViewTestCase.setUp (self)
        self.view_path = 'reservations.views.club_edit'
        self.template_name = 'reservations/club_edit.html'
        #
        # get some args for this view
        #
        cs = CourtSetup.objects.get_active (self.club)
        v = None
        while v is None:
            v = Vacancy.objects.get_free (cs,
                                          date.today ( ),
                                          Vacancy.HOURS[randint(0, 15)][0])
            v = v[0] if v else None
        self.view_args = [v.id, date.today ( ).toordinal ( )]
        
    def test_only_object_owner_has_access (self):
        BaseViewTestCase._test_only_club_has_access (self,
                                                     self.T_CLUB,
                                                     self.view_args)
        
    def test_existance_and_correct_template (self):
        BaseViewTestCase._test_existance_and_correct_template (self,
                                                               self.T_CLUB,
                                                               self.view_args)
        
        
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
