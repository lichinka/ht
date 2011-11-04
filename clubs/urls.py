from django.conf.urls.defaults import patterns

#
# Handles the views for the Clubs application
#
urlpatterns = patterns ('clubs.views',
                        (r'^edit_court_setup/(?P<cs_id>\d+)/$', 'edit_court_setup'),
                        (r'^edit_court_setup/(?P<cs_id>\d+)/(?P<c_id>\d+)/$', 'edit_court_setup'),
                        (r'^toggle_available_court/(?P<c_id>\d+)/$', 'toggle_available_court'),
                        (r'^edit_court_properties/(?P<cs_id>\d+)/(?P<c_id>\d+)/$', 'edit_court_properties'),
                        (r'^save_court_vacancy/(?P<id>\d+)/$', 'save_court_vacancy'),
                        (r'^clone_court/(?P<c_id>\d+)/$', 'clone_court'),
                        (r'^delete_court/(?P<c_id>\d+)/$', 'delete_court'),
                        (r'^clone_court_setup/(?P<cs_id>\d+)/$', 'clone_court_setup'),
                        (r'^delete_court_setup/(?P<cs_id>\d+)/$', 'delete_court_setup'),
                        (r'^toggle_active_court_setup/(?P<cs_id>\d+)/$', 'toggle_active_court_setup'))

