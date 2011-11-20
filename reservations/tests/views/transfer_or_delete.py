from random import randint

from django.core.urlresolvers import reverse

from clubs.models import CourtSetup
from ht_utils.tests import BaseViewTestCase
from reservations.models import Reservation



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

