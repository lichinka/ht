from django.conf.urls.defaults import patterns

#
# Handles the views for the Players application
#
urlpatterns = patterns ('ht_utils.views',
                        (r'^success$', 'success'))
