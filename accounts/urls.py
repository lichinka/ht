from django.contrib.auth import views as auth_views
from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template

from registration.views import activate
from registration.views import register


#
# URLs for the Accounts & django-registration applications
#
urlpatterns = patterns ('',
                        url (r'^register/$',
                             register,
                             {'template_name':  'accounts/registration/register.html',
                              'success_url':    'accounts_registration_complete',
                              'disallowed_url': 'accounts_registration_disallowed',
                              'backend':        'registration.backends.default.DefaultBackend'},
                              name='accounts_registration_register'),
                        url (r'^register/complete/$',
                             direct_to_template,
                             {'template': 'accounts/registration/registration_complete.html'},
                             name='accounts_registration_complete'),
                        url (r'^register/closed/$',
                             direct_to_template,
                             {'template': 'accounts/registration/registration_closed.html'},
                             name='accounts_registration_disallowed'),
                        #
                        # Activation keys get matched by \w+ instead of the more specific
                        # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
                        # that way it can return a sensible "invalid key" message instead of a
                        # confusing 404.
                        #
                        url (r'^activate/complete/$',
                             direct_to_template,
                             {'template': 'accounts/registration/activation_complete.html'},
                             name='accounts_registration_activation_complete'),
                        url (r'^activate/(?P<activation_key>\w+)/$',
                             activate,
                             {'template_name': 'accounts/registration/activation_error.html',
                              'success_url':   'accounts_registration_activation_complete',
                              'backend':       'registration.backends.default.DefaultBackend'},
                             name='accounts_registration_activate'),
                        #
                        # Profile-related views
                        #
                        url (r'^edit_player_profile/$', 
                             'accounts.views.edit_player_profile',
                             name='accounts_edit_player_profile'),
                        url (r'^edit_club_profile/$',
                             'accounts.views.edit_club_profile',
                             name='accounts_edit_club_profile'),
                        url (r'^profile/$',
                             'accounts.views.display_profile',
                             name='accounts_display_profile'),
                        url (r'^login/$',
                             'accounts.views.login',
                             name='accounts_login'),
                        url (r'^logout/$',
                             'accounts.views.logout',
                             name='accounts_logout'),
                        url (r'^password/change/$',
                             auth_views.password_change,
                             name='accounts_password_change'),
                        url (r'^password/change/done/$',
                             auth_views.password_change_done,
                             name='accounts_password_change_done'),
                        url (r'^password/reset/$',
                             auth_views.password_reset,
                             name='accounts_password_reset'),
                        url (r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
                             auth_views.password_reset_confirm,
                             name='accounts_password_reset_confirm'),
                        url (r'^password/reset/complete/$',
                             auth_views.password_reset_complete,
                             name='accounts_password_reset_complete'),
                        url (r'^password/reset/done/$',
                             auth_views.password_reset_done,
                             name='accounts_password_reset_done'),
                    )
