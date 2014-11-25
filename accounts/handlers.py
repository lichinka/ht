from django.db.models.signals import post_save, pre_delete
from django.contrib.auth.models import User
from django.dispatch.dispatcher import receiver

from notification import models as notification
from actstream.signals import action
from registration.signals import user_activated



@receiver (user_activated, dispatch_uid="registration_user_activated")
def user_activated_account (user, request, **kwargs):
    """
    Callback function used whenever a user activates her account.-
    """
    notification.send ([user], 'accounts_first_login')



"""
The 'club_profile_handler' is defined in 'models.py'
to avoid a cyclic import.-
"""



@receiver (post_save, sender=User, dispatch_uid="user_profile_post_save")
def link_user_with_player_profile (sender, instance, created, **kwargs):
    """
    Callback function used whenever an existing user's data are updated
    or a new user is created. In this case, a player's profile is created
    and linked to it.
    """
    if created:
        #
        # create a new player profile and link it with the user
        #
        from accounts.models import UserProfile
        pp = UserProfile.objects.create_player_profile (instance.username)
        action.send (instance, verb='has profile', target=pp)



@receiver (pre_delete, sender=User, dispatch_uid="user_profile_pre_delete")
def delete_associated_profile (sender, instance, **kwargs):
    """
    Callback function used whenever a user is to be
    deleted. It deletes the associated Player/Club Profile and
    generates a user's action in the 'activity' app.-
    """
    #
    # Make sure a player/club profile exists, associated
    # with the user profile being deleted
    #
    from accounts.models import UserProfile, ClubProfile, PlayerProfile
    prof = UserProfile.objects.get_profile (instance.username)
    if prof:
        if prof.is_player ( ):
            PlayerProfile.objects.get (pk=prof.id).delete ( )
        if prof.is_club ( ):
            ClubProfile.objects.get (pk=prof.id).delete ( )
        action.send (instance, verb='deleted', target=prof)

