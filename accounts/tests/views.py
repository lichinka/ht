from collections import deque

from django.test import Client
from django.core.urlresolvers import reverse

from ht_utils import random_ascii_string, pick_random_element
from ht_utils.tests import BaseViewTestCase
from accounts.models import UserProfile, PlayerProfile
from locations.models import City




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
        self.T_CLUB['company']    = "Ghetto d.o.o."
        self.T_CLUB['tax_number'] = 'SI 1234567890123'
        self.T_CLUB['address']    = "A totally new address 9873"
        self.T_CLUB['city']       = pick_random_element (City.objects.all ( )).pk
        self.T_CLUB['phone']      = "111 222 333 444"
        resp = self.client.post (reverse (self.view_path),
                                 self.T_CLUB,
                                 follow=True)
        self.assertContains (resp, self.T_CLUB['company'])
        self.club = UserProfile.objects.get_profile (self.T_CLUB['username'])
        self.T_CLUB['city'] = City.objects.get (pk=self.T_CLUB['city'])
        for field in ['company', 'tax_number', 'address', 'city', 'phone']:
            self.assertEquals (getattr (self.club, field, None), self.T_CLUB[field])


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
        cli = Client ( )
        view_url = reverse ('accounts.views.edit_player_profile')

        self.assertTrue (cli.login (username=self.club.user.username,
                                    password=self.T_CLUB['password']))

        resp = cli.get (view_url, follow=True)
        self.assertTrue (resp.status_code == 404,
                         'View %s did not return 404, despite a club being logged-in' % view_url)

        #
        # log the club out
        #
        cli.logout ( )

        self.assertTrue (cli.login (username=self.player.user.username,
                                    password=self.T_PLAYER['password']))

        resp = cli.get (view_url)
        self.assertTrue (resp.status_code == 200,
                         "The view %s returned %s" % (view_url,
                                                      resp.status_code))
        #
        # test view display
        #
        resp = cli.get (view_url)
        form = resp.context[-1]['form']
        first_name = form.initial['first_name']
        self.assertTrue (first_name == self.player.user.first_name,
                         "Displayed player's first name does not match")
        last_name = form.initial['last_name']
        self.assertTrue (last_name == self.player.user.last_name,
                         "Displayed player's last name does not match")
        level = form.initial['level']
        self.assertTrue (level == self.player.level,
                         "Displayed player's level does not match")
        male = form.initial['male']
        self.assertTrue (male == self.player.male,
                         "Displayed player's sex does not match")
        right_handed = form.initial['right_handed']
        self.assertTrue (right_handed == self.player.right_handed,
                         "Displayed player's handed does not match")
        #
        # test view save
        #
        first_name = random_ascii_string (form.fields['first_name'].max_length)
        last_name  = random_ascii_string (form.fields['last_name'].max_length)
        level = form.fields['level'].choices[-1][0]
        male  = False
        right_handed = False
        resp = cli.post (view_url,
                         {'user': self.player.user.id,
                          'first_name': first_name,
                          'last_name': last_name,
                          'level': level,
                          'male': male,
                          'right_handed': right_handed,
                          'next': reverse ('ht.views.home')},
                         follow=True)
        self.assertTrue (resp.status_code == 200,
                         "The view %s returned %s" % (view_url,
                                                      resp.status_code))
        context = deque (resp.context, maxlen=1)
        context = context.pop ( )
        if 'form' in context:
            self.assertEquals (context['form'].errors, None)

        self.assertEquals (resp.request['PATH_INFO'], reverse ('ht.views.home'))

        self.player = PlayerProfile.objects.get (pk=self.player.id)
        self.assertTrue (self.player.user.first_name == first_name,
                         "Player's first name does not match after saving")
        self.assertTrue (self.player.user.last_name == last_name,
                         "Player's last name does not match after saving")
        self.assertTrue (self.player.level == level,
                         "Player's level does not match after saving")
        self.assertTrue (self.player.male == male,
                         "Player's sex does not match after saving")
        self.assertTrue (self.player.right_handed == right_handed,
                         "Player's handed does not match after saving")


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

