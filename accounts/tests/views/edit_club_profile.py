import random

from django.core.urlresolvers import reverse

from locations.models import City
from ht_utils.tests.views import BaseViewTestCase



def test_club_profile_saving (instance, data, test_case, 
                              view_path='accounts_edit_club_profile'):
    """
    Tests that a ClubProfile is correctly saved via the view.
    This method returns the 'response' object used, after all
    assertions are successful.
    
             instance: the ClubProfile instance to test;
                 data: a dictionary which keys are field names of the
                       tested instance;
            test_case: the instance of the test case being executed.
                       The client and assertions are accessed through it;
            view_path: path of the tested view (without reversing!).-
          
    """
    data['company']    = "Ghetto d.o.o."
    data['tax_number'] = 'SI 1234567890123'
    data['address']    = "A totally new address 9873"
    data['city']       = random.choice (City.objects.all ( )).pk
    data['phone']      = "111 222 333 444"
    changed_data = dict ([(k, data[k]) for k in ('company', 
                                                 'tax_number', 
                                                 'address',
                                                 'city',
                                                 'phone')])
    test_case.view_path = view_path
    resp = test_case._test_model_instance_save (instance, changed_data)
    test_case.assertContains (resp, data['company'])
    return resp
    
    

class EditClubProfileTest (BaseViewTestCase):
    """
    All the test cases for the views of this app.-
    """
    def setUp (self):
        """
        Creates a club and player used during testing.-
        """
        self._create_club ( )
        self._create_player ( )


    def test_edit_club_profile (self):
        """
        Checks the behavior of accounts.views.edit_club_profile.-
        """
        self.view_path = 'accounts_edit_club_profile'
        self.template_name = 'accounts/edit_club_profile.html'
        self._test_existance_and_correct_template (login_info={'username': self.T_CLUB['username'],
                                                               'password': self.T_CLUB['password']})
        self._test_only_club_has_access ( )
        #
        # test displayed data is correct
        #
        self.client.login (username=self.T_CLUB['username'],
                           password=self.T_CLUB['password'])
        resp = self.client.get (reverse (self.view_path))

        self.assertContains (resp, self.club.address, 1)
        self.assertContains (resp, unicode (self.club.city), 1)
        self.assertContains (resp, self.club.phone, 1)
        self.assertContains (resp, self.club.company, 1)
        #
        # test saved data is correct
        #
        test_club_profile_saving (self.club, self.T_CLUB, self)
