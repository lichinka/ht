from django.conf.urls.defaults import patterns, url

#
# Handles the views for the Accounts application
#
urlpatterns = patterns ('accounts.views',
                        (r'^register/$', 'register'),
                        (r'^edit_player_profile/$', 'edit_player_profile'),
                        url (r'^edit_club_profile/$',
                             'edit_club_profile',
                             name='accounts_edit_club_profile'),
                        (r'^login/$', 'login'),
                        url (r'^profile/$', 'display_profile',
                             name='accounts_display_profile'),
                        (r'^logout/$', 'logout'))
