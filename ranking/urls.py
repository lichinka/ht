from django.conf.urls.defaults import patterns

#
# Handles the views for the Ranking application
#
urlpatterns = patterns ('ranking.views',
                        (r'^display_ranking$', 'display_ranking'),
                        (r'^display_matches/(?P<id>\d+)/$', 'display_matches'),
                        (r'^enter_result$', 'enter_result'),
                        (r'^comment_match/(?P<id>\d+)/$', 'comment_match'),
                        (r'^challenge_result/(?P<plr_id>\d+)/(?P<mat_id>\d+)/$', 'challenge_result'))
