from django.conf.urls.defaults import patterns

#
# Handles the views for the Players application
#
urlpatterns = patterns ('players.views',
                        (r'^add_vacancy$', 'add_vacancy'),
                        (r'^edit_vacancy$', 'edit_vacancy'),
                        (r'^delete_vacancy/(?P<id>\d+)/$', 'delete_vacancy'),
                        (r'^search_opponent$', 'search_opponent'),
                        (r'^invite_player/(?P<id>\d+)/$', 'invite_player'))
