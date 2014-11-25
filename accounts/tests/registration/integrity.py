from registration.models import RegistrationProfile
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from notification.models import Notice
from ht_utils.tests.views import BaseViewTestCase


class NotificationIntegrityTest (BaseViewTestCase):
    def setUp(self):
        """
        Avoid calling the parent's setUp method.-
        """
        pass

    def test_notification_sent_when_user_activates_account (self):
        """
        A Notification has to be sent whenever a user actives a new account.-
        """
        success_redirect = 'http://testserver%s' % reverse ('accounts_registration_activation_complete')
        #
        # register an account ...
        #
        self.client.post (reverse ('accounts_registration_register'),
                          data={'username': 'alice',
                                'email': 'alice@example.com',
                                'password1': 'swordfish',
                                'password2': 'swordfish'})
        #
        # ... and activate it
        #
        usr = User.objects.get (username='alice')
        profile = RegistrationProfile.objects.get (user=usr)
        response = self.client.get (reverse ('accounts_registration_activate',
                                    kwargs={'activation_key': profile.activation_key}),
                                    follow=True)
        self.failUnless (User.objects.get (username='alice').is_active)
        #
        # check the corresponding notification has been sent
        #
        q = Notice.objects.notices_for (user=usr).filter (notice_type__label=
                                                          'accounts_first_login')
        self.assertEquals (q.count ( ), 1)


