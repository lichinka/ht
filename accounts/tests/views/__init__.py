import random
from collections import deque

from django.test import Client
from django.core.urlresolvers import reverse

from ht_utils import random_ascii_string
from accounts.models import PlayerProfile
from locations.models import City
from ht_utils.tests.views import BaseViewTestCase

from edit_club_profile import *



class ViewTest (BaseViewTestCase):
    """
    All the test cases for the views of this app.-
    """
    def setUp (self):
        """
        Creates a club and a player used during testing.-
        """
        self._create_club ( )
        self._create_player ( )


    def test_register (self):
        """
        Checks the behavior of accounts.views.register.-
        """
        cli = Client ( )

        view_url = reverse ('accounts.views.register')
        resp = cli.get (view_url)
        self.assertTrue (resp.status_code == 200,
                         "The view %s returned %s" % (view_url,
                                                      resp.status_code))

        resp = cli.post (view_url,
                         {'email': 'iztok', 'pass2': 'iztok', 'pass1': 'iztok', })
        form = resp.context[-1]['form']
        self.assertTrue ('email' in form.errors.keys ( ),
                         'View %s did not recognize an invalid email address' % view_url)

        resp = cli.post (view_url,
                         {'email': 'iztok.fajdiga@mobitel.si', 'pass2': 'izt', 'pass1': 'iztok', })
        form = resp.context[-1]['form']
        self.assertTrue ('__all__' in form.errors.keys ( ),
                         'View %s did not recognize no-matching passwords' % view_url)

        resp = cli.post (view_url,
                         {'email': self.club.user.username, 'pass2': 'iztok', 'pass1': 'iztok', })
        form = resp.context[-1]['form']
        self.assertTrue ('email' in form.errors.keys ( ),
                         'View %s did not recognize the username %s was already taken' % (view_url,
                                                                                          self.club.user.username))

        self.assertTrue (cli.login (username=self.club.user.username,
                                    password=self.T_CLUB['password']))

        resp = cli.get (view_url, follow=True)
        self.assertEquals (resp.request['PATH_INFO'], reverse ('ht.views.home'),
                           'View %s did not redirect to home page, despite %s being logged-in' % (view_url,
                                                                                                  self.club))
        #
        # log the club out
        #
        cli.logout ( )

        resp = cli.post (view_url,
                         {'email': 'iztok.fajdiga@mobitel.si', 'pass2': 'iztok', 'pass1': 'iztok', },
                         follow=True)
        next_url = reverse ('accounts.views.edit_player_profile')
        next_url = next_url.split ('/')[2]
        self.assertTrue (next_url in resp.request['PATH_INFO'],
                         'View %s did not redirect to %s after registering a new user' % (view_url,
                                                                                          next_url))

    def test_edit_player_profile (self):
        """
        Checks the behavior of accounts.views.edit_player_profile.-
        """
        self.view_path = 'accounts_edit_player_profile'
        self.template_name = 'accounts/edit_player_profile.html'
        self._test_existance_and_correct_template (login_info={'username': self.T_PLAYER['username'],
                                                               'password': self.T_PLAYER['password']})
        self._test_only_player_has_access ( )
        #
        # test displayed data is correct
        #
        resp = self.client.get (reverse (self.view_path))
        form = resp.context[-1]['form']
        self.assertContains (resp, self.player.user.first_name, 2)
        self.assertContains (resp, self.player.user.last_name, 2)
        self.assertEquals (form.initial['level'], self.player.level)
        self.assertEquals (form.initial['male'], self.player.male)
        self.assertEquals (form.initial['right_handed'], self.player.right_handed)
        #
        # test data is correctly saved
        #
        self.T_PLAYER['first_name']   = random_ascii_string (form.fields['first_name'].max_length)
        self.T_PLAYER['last_name']    = random_ascii_string (form.fields['last_name'].max_length)
        self.T_PLAYER['level']        = random.choice (PlayerProfile.LEVELS)[0]
        self.T_PLAYER['male']         = random.randint (1, 2) % 2 == 0
        self.T_PLAYER['right_handed'] = random.randint (1, 9) % 3 == 0
        
        resp = self._test_model_instance_save (self.player.user, self.T_PLAYER, 
                                               ('first_name', 'last_name'))
        self._test_model_instance_save (self.player, self.T_PLAYER,
                                        ('level', 'male', 'right_handed'))
        self.assertContains (resp, self.T_PLAYER['first_name'], 2)
        self.assertContains (resp, self.T_PLAYER['last_name'], 2)


    def test_login (self):
        """
        Checks the behavior of accounts.views.login.-
        """
        cli = Client ( )
        view_url = reverse ('accounts.views.login')
        resp = cli.get (view_url)
        self.assertTrue (resp.status_code == 200,
                         "The view %s returned %s" % (view_url,
                                                      resp.status_code))

    def test_logout (self):
        """
        Checks the behavior of accounts.views.logout.-
        """
        cli = Client ( )
        view_url = reverse ('accounts.views.logout')
        resp = cli.get (view_url, follow=True)
        self.assertTrue (resp.status_code == 200,
                         "The view %s returned %s" % (view_url,
                                                      resp.status_code))
        self.assertEquals (resp.request['PATH_INFO'], reverse('ht.views.home'),
                           'View %s did not redirect to home page' % view_url)

