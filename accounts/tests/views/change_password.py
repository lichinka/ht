from django.core.urlresolvers import reverse

from ht_utils.tests.views import BaseViewTestCase



class ChangePasswordViewTest (BaseViewTestCase):
    """
    All the test cases for this view.-
    """
    def setUp (self):
        """
        Creates a club and a player used during testing.-
        """
        self._create_club ( )
        self._create_player ( )
        self.view_path = 'accounts_change_password'
        self.template_name = 'accounts/change_password.html'


    def test_club_display (self):
        """
        Checks the view is correctly displayed for clubs.-
        """
        self._test_existance_and_correct_template (login_info={'username': self.T_CLUB['username'],
                                                               'password': self.T_CLUB['password']})
    
    def test_club_save (self):
        """
        Checks the view is correctly saving the data to the DB.-
        """
        self.client.login (username=self.T_CLUB['username'],
                           password=self.T_CLUB['password'])
        #
        # test changed password is correctly saved
        #
        self.T_CLUB['old_password']  = self.T_CLUB['password']
        self.T_CLUB['new_password1'] = 'swordfish'
        self.T_CLUB['new_password2'] = 'swordfish'
        self.client.post (reverse (self.view_path),
                          self.T_CLUB,
                          follow=True)
        #
        # test club can login with the new password
        #
        self.client.logout ( )
        self._test_existance_and_correct_template (login_info={'username': self.T_CLUB['username'],
                                                               'password': self.T_CLUB['new_password1']})
    