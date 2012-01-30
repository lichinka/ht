from django.conf.urls.defaults import patterns, url

#
# Handles the views for the Players application
#
urlpatterns = patterns ('reservations.views',
                        (r'^search$', 'search'),
                        (r'^club_view$', 'club_view'),
                        (r'^cancel/(?P<r_id>\d+)/$', 'cancel'),
                        url (r'^player_edit/(?P<v_id>\d+)/(?P<ordinal_date>\d+)/$',
                             'player_edit',
                             name='reservations_edit_player'),
                        url (r'^club_edit/(?P<v_id>\d+)/(?P<ordinal_date>\d+)/$',
                             'club_edit',
                             name='reservations_edit_club'),
                        (r'^transfer_or_delete/(?P<cs_id>\d+)/$', 'transfer_or_delete'),
                        (r'^transfer_or_delete/(?P<cs_id>\d+)/(?P<c_id>\d+)/$', 'transfer_or_delete')
                        )
