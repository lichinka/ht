from collections import deque

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

import ht_utils
from accounts.models import UserProfile, ClubProfile, PlayerProfile
from locations.models import City



class TemplateTagTest (TestCase):
    """
    All the test cases for the template tags of this app.-
    """
    pass


class ViewTest (TestCase):
    """
    All the test cases for the views of this app.-
    """
    def setUp (self):
        """
        Creates a club and a player used during testing.-
        """
        c = User.objects.create_user ('club@nowhere.si', 'club@nowhere.si', 'pass')
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")
        p = User.objects.create_user ('some_player@somewhere.si', 'some_player@somewhere.si', 'pass')
        self.player = UserProfile.objects.create_player_profile (p.username)
        self.player.level = 'I'
        self.player.male = True
        self.player.right_handed = False
        self.player.save ( )


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

        self.assertTrue (cli.login (username=self.club.user.username, password='pass'),
                         'Could not log %s in' % self.club)

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
                                    password='pass'),
                         'Could not log club %s in' % self.club)

        resp = cli.get (view_url, follow=True)
        self.assertTrue (resp.status_code == 404,
                         'View %s did not return 404, despite a club being logged-in' % view_url)

        #
        # log the club out
        #
        cli.logout ( )

        self.assertTrue (cli.login (username=self.player.user.username,
                                    password='pass'),
                         'Could not log player %s in' % self.player)

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
        first_name = ht_utils.random_ascii_string (form.fields['first_name'].max_length)
        last_name  = ht_utils.random_ascii_string (form.fields['last_name'].max_length)
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



class UserProfileTest (TestCase):
    """
    All tests regarding the UserProfile model.
    """
    def setUp (self):
        """
        Creates some test players and clubs used during testing.-
        """
        p = User.objects.create_user ('test_player', 'player@nowhere.si', 'pass')
        UserProfile.objects.create_player_profile (p)
        c = User.objects.create_user ('test_club', 'club@nowhere.si', 'pass')
        UserProfile.objects.create_club_profile (c,
                                                 "Postal address 1231",
                                                 City.objects.all ( )[0],
                                                 "111-222-333",
                                                 "The best tennis club d.o.o.")


    def test_player_cannot_be_club (self):
        """
        Checks that a player cannot have a club's profile associated.-
        """
        pp = UserProfile.objects.get_profile ('test_player')
        cp = UserProfile.objects.create_club_profile (pp.user.username,
                                                      "Some address",
                                                      City.objects.all ( )[0],
                                                      "Some phone",
                                                      "Some company")
        self.assertTrue (cp is None,
                         "A club's profile has been associated with an existing player")
        self.assertTrue (len (ClubProfile.objects.filter (user__username='test_player')) == 0,
                         "A club's profile has been associated with an existing player")


    def test_player_profile_creation (self):
        """
        Checks that the player profile is correctly created.-
        """
        up = UserProfile.objects.get_profile ('test_player')

        self.assertTrue (up.is_player ( ),
                         "The created player's profile is incorrect")
        self.assertTrue (up.is_club ( ) == False,
                         "The created player's profile is incorrect")
        self.assertTrue (up.level == 'B')
        self.assertTrue (up.male)
        self.assertTrue (up.right_handed)


    def test_player_profile_deletion (self):
        """
        Checks that the corresponding profile is deleted with the user.-
        """
        u = User.objects.get (username='test_player')
        up = UserProfile.objects.get_profile (u.username)
        u.delete ( )
        self.assertTrue (len (PlayerProfile.objects.filter (pk=up.id)) == 0,
                         "The related player's profile has not been deleted")


    def test_club_profile_creation (self):
        """
        Checks that the club profile is correctly created.-
        """
        up = UserProfile.objects.get_profile ('test_club')

        self.assertTrue (up.is_club ( ),
                         "The created club's profile is incorrect")
        self.assertTrue (up.is_player ( ) == False,
                         "The created club's profile is incorrect")
        self.assertTrue (up.address == 'Postal address 1231')
        self.assertTrue (up.city == City.objects.all ( )[0])
        self.assertTrue (up.phone == '111-222-333')
        self.assertTrue (up.company == 'The best tennis club d.o.o.')


    def test_club_profile_deletion (self):
        """
        Checks that the corresponding profile is deleted with the user.-
        """
        u = User.objects.get (username='test_club')
        up = UserProfile.objects.get_profile (u.username)
        u.delete ( )
        self.assertTrue (len (ClubProfile.objects.filter (pk=up.id)) == 0,
                         "The related club's profile has not been deleted")

