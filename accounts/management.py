from django.conf import settings
from django.db.models.signals import post_syncdb
from django.utils.translation import ugettext_noop as _



#
# Add notification types used by this module:
#
#    'accounts_first_login'
#
if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification                                                                                                    

    def create_notice_types (app, created_models, verbosity, **kwargs):
        notification.create_notice_type ('accounts_first_login',
                                         _('Welcome!'),
                                         _('short instructions for new users'))

    post_syncdb.connect (create_notice_types, sender=notification)