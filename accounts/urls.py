from django.conf.urls.defaults import patterns, url

#
# Handles the views for the Accounts application
#
urlpatterns = patterns ('accounts.views',
                        (r'^register/$', 'register'),
                        (r'^edit_player_profile/$', 'edit_player_profile'),
                        (r'^login/$', 'login'),
                        url (r'^profile/$', 'display_profile', name='accounts_profile'),
                        (r'^logout/$', 'logout'))
