import random

from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from reservations.models import Reservation
from ht_utils.tests.views import BaseViewTestCase
from accounts.tests.views.edit_club_profile import test_club_profile_saving




class IntegrityTestCase (BaseViewTestCase):
    def setUp (self):
        self._create_player ( )
        self._add_vacancy_prices ( )
        self.user_type = ContentType.objects.get (app_label="auth",
                                                  model="user")

    def test_player_profile_creation_is_tracked (self):
        """
        Makes sure the player's profile creation is being tracked.-
        """
        self.client.login (username=self.T_PLAYER['username'],
                           password=self.T_PLAYER['password'])
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': self.player.user.pk}))
        self.assertContains (resp, self.T_PLAYER['username'])
        self.assertContains (resp, 'has profile', 1)
        self.assertContains (resp, unicode (self.player))
        
        
    def test_club_profile_is_tracked (self):
        """
        Checks that an action is saved whenever a new
        club profile is created.-
        """
        #
        # club profile creation
        #
        self.client.login (username=self.T_CLUB['username'],
                           password=self.T_CLUB['password'])
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': self.club.user.pk}))
        self.assertContains (resp, self.T_CLUB['username'])
        self.assertContains (resp, 'created', 1)
        self.assertContains (resp, unicode (self.club))
        #
        # club profile change
        #
        test_club_profile_saving (self.club, self.T_CLUB, self)
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': self.club.user.pk}))
        self.assertContains (resp, self.T_CLUB['username'])
        self.assertContains (resp, 'updated', 1)
        self.assertContains (resp, unicode (self.club))


    def test_player_booking_is_tracked (self):
        """
        Checks that a reservation created by a player correctly
        triggers the activity tracking system.-
        """
        #
        # reservation creation
        #
        self.client.login (username=self.T_PLAYER['username'],
                           password=self.T_PLAYER['password'])
        user = User.objects.get (username=self.T_PLAYER['username'])
        v = random.choice (self.vacancy_list)
        self.assertIsNotNone (v)
        r = Reservation.objects.book (for_date=date.today ( ),
                                      vacancy=v,
                                      user=user,
                                      description="Test reservation")
        self.assertIsNotNone (r)
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': user.pk}))
        self.assertContains (resp, self.T_PLAYER['username'])
        self.assertContains (resp, 'created')
        #
        # reservation update
        #
        view_url = reverse ('reservations_edit_player',
                                         kwargs={'v_id': r.vacancy.pk,
                                                 'ordinal_date': r.for_date.toordinal ( )})
        resp = self.client.get (view_url)
        form = resp.context[-1]['form']
        resp = self.client.post (view_url,
                                 {'created_on': form.instance.created_on,
                                  'for_date': form.instance.for_date,
                                  'type': form.instance.type,
                                  'user': form.instance.user.id,
                                  'vacancy': form.instance.vacancy.id,
                                  'repeat': False,
                                  'repeat_until': form.instance.for_date},
                                 follow=True)
        self.assertEquals (resp.status_code, 200)
        try:
            form = resp.context[-1]['form']
            self.assertEqual (len (form.errors.keys ( )), 0)
        except KeyError:
            #
            # the form redirected successfully if there is no 'form'
            #
            pass
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': user.pk}))
        self.assertContains (resp, self.T_PLAYER['username'])
        self.assertContains (resp, 'updated', 1)
        self.assertContains (resp, unicode (r), 2)


    def test_club_booking_is_tracked (self):
        """
        Checks that a reservation created by a club correctly
        triggers the activity tracking system.-
        """
        #
        # reservation creation
        #
        self.client.login (username=self.T_CLUB['username'],
                           password=self.T_CLUB['password'])
        user = User.objects.get (username=self.T_CLUB['username'])
        v = random.choice (self.vacancy_list)
        self.assertIsNotNone (v)
        r = Reservation.objects.book (for_date=date.today ( ),
                                      vacancy=v,
                                      user=user,
                                      description="Test reservation")
        self.assertIsNotNone (r)
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': user.pk}))
        self.assertContains (resp, self.T_CLUB['username'])
        self.assertContains (resp, 'created')
        self.assertContains (resp, unicode (r))
        #
        # reservation update
        #
        view_url = reverse ('reservations_edit_club',
                                         kwargs={'v_id': r.vacancy.pk,
                                                 'ordinal_date': r.for_date.toordinal ( )})
        resp = self.client.get (view_url)
        form = resp.context[-1]['form']
        resp = self.client.post (view_url,
                                 {'created_on': form.instance.created_on,
                                  'for_date': form.instance.for_date,
                                  'type': form.instance.type,
                                  'description': 'Updated test reservation',
                                  'user': form.instance.user.id,
                                  'vacancy': form.instance.vacancy.id,
                                  'repeat': True,
                                  'repeat_until': form.instance.for_date + timedelta (days=2)},
                                 follow=True)
        self.assertEquals (resp.status_code, 200)
        form = resp.context[-1]['form']
        self.assertEqual (len (form.errors.keys ( )), 0)
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': user.pk}))
        self.assertContains (resp, self.T_CLUB['username'])
        self.assertContains (resp, 'updated', 1)
        self.assertContains (resp, unicode (r), 2)

    def test_user_own_activity (self):
        #
        # log the club in via the login page to
        # generate an action
        #
        resp = self.client.post (reverse ('accounts.views.login'),
                                 {'username': self.T_CLUB['username'],
                                  'password': self.T_CLUB['password']},
                                 follow=True)
        self.assertEqual (resp.status_code, 200)
        #
        # check the 'log in' action has been saved
        #
        user = get_object_or_404 (User, username=self.T_CLUB['username'])
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': user.pk}))
        self.assertContains (resp, self.T_CLUB['username'])
        self.assertContains (resp, 'logged in')
        #
        # log the club out via the page to
        # generate an action
        #
        resp = self.client.get (reverse ('accounts.views.logout'),
                                follow=True)
        self.assertEqual (resp.status_code, 200)
        #
        # check the 'log out' action is correctly saved
        # (any user should be logged id to watch the activities)
        #
        self.client.login (username=self.T_PLAYER['username'],
                           password=self.T_PLAYER['password'])
        resp = self.client.get (reverse ('actstream_actor',
                                         kwargs={'content_type_id': self.user_type.pk,
                                                 'object_id': user.pk}))
        self.assertContains (resp, self.T_CLUB['username'])
        self.assertContains (resp, 'logged out')
