from random import randint
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from django.test import TestCase
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
from django.contrib.auth.models import User

from ht_utils import number_to_default_locale, pick_random_element
from ht_utils.tests import BaseViewTestCase
from clubs.models import CourtSetup, Court, Vacancy
from accounts.models import UserProfile
from locations.models import City
from clubs.templatetags import vacancy_tags
from reservations.models import Reservation
from clubs.templatetags.vacancy_tags import vacancy_prices_per_day
from django.core.exceptions import ObjectDoesNotExist



class DeleteCourtSetupTest (BaseViewTestCase):
    """
    All the test cases for this view.-
    """
    def test_delete_court_setup_without_reservations (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        cs_count = CourtSetup.objects.all ( ).aggregate (Count('id'))
        #
        # get a court setup 
        #
        cs = pick_random_element (self.cs_list)
        #
        # delete all its reservations
        #
        for court in Court.objects.filter (court_setup=cs):
            Court.objects.delete_reservations (court)
        #
        # now, delete the court setup without reservations
        #
        view_url = reverse ('clubs.views.delete_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'accounts/display_club_profile.html')
        self.assertEquals (cs_count['id__count'] - 1,
                           CourtSetup.objects.all ( ).aggregate (Count('id'))['id__count'])
        
    def test_redirect_if_court_setup_has_reservations (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        #
        # get a court setup WITH reservations
        #
        for cs in self.cs_list:
            r = Reservation.objects.by_court_setup (cs)
            if r:
                cs = CourtSetup.objects.get (pk=cs.id)
                break
        self.assertIsInstance (cs, CourtSetup)
        view_url = reverse ('clubs.views.delete_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, 'ht_utils/success.html')
        
            
        
class ToggleActiveCourtSetupTest (BaseViewTestCase):
    def test (self):
        """
        Checks the behavior of clubs.views.toggle_active_court_setup.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # check that the active court setup cannot be deactivated
        #
        cs = CourtSetup.objects.get_active (self.club)
        view_url = reverse ('clubs.views.toggle_active_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        cs = CourtSetup.objects.get (pk=cs.id)
        self.assertEquals (cs.is_active, True)
        #
        # check that there is always strictly one active court setup
        #
        cs = CourtSetup.objects.filter (club=self.club) \
                               .filter (is_active=True) \
                               .aggregate (Count ('id'))
        self.assertEquals (int (cs['id__count']), 1)
        #
        # check that some non-active court setup is correctly activated
        #
        cs = CourtSetup.objects.filter (club=self.club).filter (is_active=False)
        if cs:
            cs = cs[0]
            view_url = reverse ('clubs.views.toggle_active_court_setup',
                                args=[cs.id])
            resp = self.cli.get (view_url, follow=True)
            self.assertEquals (resp.status_code, 200)
            cs = CourtSetup.objects.get (pk=cs.id)
            self.assertEquals (cs.is_active, True)
        #
        # check that there is always strictly one active court setup
        #
        cs = CourtSetup.objects.filter (club=self.club) \
                               .filter (is_active=True) \
                               .aggregate (Count ('id'))
        self.assertEquals (int (cs['id__count']), 1)
        
            
class EditCourtSetupTest (BaseViewTestCase):
    def test (self):
        """
        Checks the behavior of clubs.views.edit_court_setup.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # check that the displayed data matches the test data
        #
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        for c in courts:
            view_url = reverse ('clubs.views.edit_court_setup',
                                args=[cs.id, c.id])
            resp = self.cli.get (view_url)
            self.assertTrue (resp.status_code == 200,
                             "The view %s returned %s" % (view_url,
                                                          resp.status_code))
            
            
class SaveCourtVacancyTest (BaseViewTestCase): 
    def test (self):
        """
        Checks the correct behavior of clubs.views.save_court_vacancy.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        for c in courts:
            court_prices = {}
            for h, hour in Vacancy.HOURS:
                prices = vacancy_prices_per_day (c, h)
                prices = dict (prices['prices'])
                for k in prices.keys ( ):
                    val = float (k.split ('_')[1]) / 10.0
                    prices[k] = '%10.2f' % val
                court_prices = dict (court_prices, **prices)
            
            view_url = reverse ('clubs.views.save_court_vacancy',
                                args=[c.id])        
            resp = self.cli.post (view_url, 
                                  court_prices, 
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            #
            # check that the saved prices match
            #
            v_ids = [ int (k.split('_')[1]) for k in court_prices.keys ( ) ]
            vacancy_list = Vacancy.objects.filter (id__in=v_ids)
            for v in vacancy_list:
                expected_val = float (v.id) / 10.0
                self.assertEquals (v.price, Decimal ('%10.2f' % expected_val))
                
