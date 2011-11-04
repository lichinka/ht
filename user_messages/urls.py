from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to

from user_messages.views import inbox, outbox, compose, reply
from user_messages.views import view, delete, undelete, trash, feedback


urlpatterns = patterns ('',
        url(r'^$', redirect_to, {'url': 'inbox/'}, name='user_messages_redirect'),
        url(r'^inbox/$', inbox, name='user_messages_inbox'),
        url(r'^outbox/$', outbox, name='user_messages_outbox'),
        url(r'^compose/$', compose, name='user_messages_compose_empty'),
        url(r'^compose/(?P<recipient>[\w.@+-]+)/(?P<subject>[\w.@+-]+)/$', 
                compose, name='user_messages_compose'),
        url(r'^reply/(?P<message_id>[\d]+)/$', reply, name='user_messages_reply'),
        url(r'^view/(?P<message_id>[\d]+)/$', view, name='user_messages_detail'),
        url(r'^delete/(?P<message_id>[\d]+)/$', delete, name='user_messages_delete'),
        url(r'^undelete/(?P<message_id>[\d]+)/$', undelete, name='user_messages_undelete'),
        url(r'^trash/$', trash, name='user_messages_trash'),
        url (r'^feedback/$', feedback),
)
