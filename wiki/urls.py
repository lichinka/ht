from django.conf.urls.defaults import patterns

#
# Handles the views for the Wiki application
#
urlpatterns = patterns ('wiki.views',
                        (r'^$', 'index'),
                        (r'^edit/(?P<article_id>\d+)/$', 'edit'),
                        (r'^preview/(?P<article_id>\d+)/$', 'preview'))
