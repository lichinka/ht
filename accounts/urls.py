from django.conf.urls.defaults import patterns

#
# Handles the views for the Accounts application
#
urlpatterns = patterns ('accounts.views',
                        (r'^register$', 'register'),
                        (r'^edit_player_profile$', 'edit_player_profile'),
                        (r'^login$', 'login'),
                        (r'^display_profile$', 'display_profile'),
                        (r'^logout$', 'logout'))
