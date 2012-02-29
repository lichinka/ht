from django.conf.urls.defaults import patterns, url

from .views import add, change, delete



urlpatterns = patterns ('accounts.avatar.views',
    url (r'^add/$', 
         add, 
         {'template_name': 'accounts/avatar/change.html',},
         name='avatar_add'),
    url (r'^change/$', 
         change,
         {'template_name': 'accounts/avatar/change.html',},
         name='avatar_change'),
    url (r'^delete/$', 
         delete,
         {'template_name': 'accounts/avatar/delete.html',},
         name='avatar_delete'),
    url('^render_primary/(?P<user>[\+\w]+)/(?P<size>[\d]+)/$', 'render_primary', name='avatar_render_primary'),    
)
