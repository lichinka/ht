from django.conf.urls.defaults import patterns

#
# Handles the views for the Players application
#
urlpatterns = patterns ('reservations.views',
                        (r'^search$', 'search'),
                        (r'^club_view$', 'club_view'),
                        (r'^cancel/(?P<r_id>\d+)/$', 'cancel'),
                        (r'^player_edit/(?P<v_id>\d+)/(?P<ordinal_date>\d+)/$', 'player_edit'),
                        (r'^club_edit/(?P<vid>\d+)/(?P<ordinal_date>\d+)/$', 'club_edit'),
                        (r'^transfer_or_delete/(?P<cs_id>\d+)/$', 'transfer_or_delete'),
                        (r'^transfer_or_delete/(?P<cs_id>\d+)/(?P<c_id>\d+)/$', 'transfer_or_delete')
                        )
