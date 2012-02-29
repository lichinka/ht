from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover ( )

urlpatterns = patterns ('',
    # url(r'^hocemtenis/', include('hocemtenis.foo.urls')),

    url (r'^$', 'ht.views.home', name='home'),
    url (r'^tos/$',
         direct_to_template,
         {'template': 'terms_of_service.html'},
         name='terms_of_service'),
    url (r'^wiki/', include ('wiki.urls')),
    url (r'^accounts/', include ('accounts.urls')),
    url (r'^clubs/', include ('clubs.urls')),
    url (r'^players/', include ('players.urls')),
    url (r'^reservations/', include ('reservations.urls')),
    url (r'^ranking/', include ('ranking.urls')),
    url (r'^user_messages/', include ('user_messages.urls')),
    url (r'^comments/', include ('comments.urls')),
    url (r'^activity/', include ('actstream.urls')),
    
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)

#
# Serve uploaded files only during development
#
if settings.DEBUG:
    urlpatterns += patterns ('',
        url (r'^media/(?P<path>.*)$',
             'django.views.static.serve',
             {'document_root': '%s/' % settings.MEDIA_ROOT,}),
   )

