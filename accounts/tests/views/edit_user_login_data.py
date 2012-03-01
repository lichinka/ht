from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from ht_utils.tests.views import BaseViewTestCase



class EditUserLoginDataViewTest (BaseViewTestCase):
    """
    All the test cases for the views of this app.-
    """
    def setUp (self):
        """
        Creates a club and a player used during testing.-
        """
        self.view_path = 'accounts_edit_user_login_data'
        self.template_name = 'accounts/edit_user_login_data.html'
        self._create_club ( )
        self._create_player ( )


    def test_club_display (self):
        """
        Checks the view is correctly displayed for clubs.-
        """
        self._test_existance_and_correct_template (login_info={'username': self.T_CLUB['username'],
                                                               'password': self.T_CLUB['password']})
        #
        # test displayed data is correct
        #
        resp = self.client.get (reverse (self.view_path))
        form = resp.context[-1]['form']
        self.assertContains (resp, self.club.user.username)
        self.assertContains (resp, self.club.user.email, 1)
        self.assertEquals (form.initial['username'], self.club.user.username)
        self.assertEquals (form.initial['email'],    self.club.user.email)
   
    
    def test_club_save (self):
        """
        Checks the view is correctly saving the data to the DB.-
        """
        self.client.login (username=self.T_CLUB['username'],
                           password=self.T_CLUB['password'])
        #
        # test changed email is correctly saved
        #
        self.T_CLUB['email'] = 'clubs_new_email@email.com'
        self._test_model_instance_save (self.club.user, self.T_CLUB, 
                                        ('email',))
        #
        # test username cannot be changed
        #
        self.T_CLUB['username'] = 'new_username_is_not_allowed'
        self.client.post (reverse (self.view_path),
                          {'username': self.T_CLUB['username'],})
        user = User.objects.get (pk=self.club.user.id)
        self.assertNotEquals (user.username, self.T_CLUB['username'])
        