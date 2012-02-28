from abc import abstractmethod

from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_delete
from django.contrib.auth.models import User

from actstream import action
from locations.models import City



class UserProfileManager (models.Manager):
    def get_players (self):
        """
        Returns all player profiles.-
        """
        return PlayerProfile.objects.all ( )


    def get_profile (self, username):
        """
        Returns the profile of the correct type (ie. player or club).-
        """
        ret_value = None
        u = User.objects.get (username=username)
        pp = PlayerProfile.objects.filter (user=u)
        if pp:
            ret_value = PlayerProfile.objects.get (user=u)

        cp = ClubProfile.objects.filter (user=u)
        if cp:
            ret_value = ClubProfile.objects.get (user=u)

        return ret_value


    def create_player_profile (self, username):
        """
        Associates a player profile with the received user and returns it.-
        """
        if self.get_profile (username) is None:
            u = User.objects.get (username=username)
            pp = PlayerProfile.objects.create (level='B',
                                               user=u)
            return pp
        else:
            #
            # return this player's existing profile
            #
            return self.get_profile (username)


    def create_club_profile (self, username, address, city, phone, company):
        """
        Associates a club profile to the received user. Because every created
        user is always first a player, the (possibly) existing player profile
        connected with the received 'username' is deleted, and thus the user
        is transformed from player to club.-
        """
        if self.get_profile (username) is None:
            u = User.objects.get (username=username)
            cp = ClubProfile.objects.create (user=u,
                                             address=address,
                                             city=city,
                                             phone=phone,
                                             company=company)
            return cp
        else:
            #
            # replace the (possible) player's profile with a club's one
            #
            if self.get_profile (username).is_player ( ):
                PlayerProfile.objects.filter (user__username=username).delete ( )
                u = User.objects.get (username=username)
                cp = ClubProfile.objects.create (user=u,
                                                 address=address,
                                                 city=city,
                                                 phone=phone,
                                                 company=company)
                return cp
            else:
                #
                # return the existing club profile
                #
                return self.get_profile (username)


class UserProfile (models.Model):
    """
    Holds extra data about the registered user of the site.
    If the foreign key to 'PlayerProfile' exists, then the user is
    registered as a player. When the foreign key to 'ClubProfile'
    exists, the user is registered as a club.
    It is an error for both foreign keys to be NULL (or None).-
    """
    user = models.ForeignKey (User,
                              unique=True,
                              blank=True)
    objects = UserProfileManager ( )

    class Meta:
        abstract = True

    @abstractmethod
    def is_player (self):
        """
        Returns TRUE if this profile belongs to a Player.-
        """
        return False

    @abstractmethod
    def is_club (self):
        """
        Returns TRUE is this profile belongs to a Club.-
        """
        return False

    def __unicode__ (self):
        return "Profile data for (%s)" % self.user.username



class PlayerProfile (UserProfile):
    """
    Holds extra data about the registered player.-
    """
    LEVELS = (('B', _('Beginner')),
              ('I', _('Intermediate')),
              ('A', _('Advanced')),
              ('F', _('Registered')))
    level = models.CharField (max_length=1,
                              choices=LEVELS,
                              default='B')
    male = models.BooleanField (default=True)
    right_handed = models.BooleanField (default=True)

    def clean (self):
        """
        Don't allow a player to have a club profile.-
        """
        if ClubProfile.objects.filter (user=self.user):
            raise ValidationError (_('This user has already been assigned a club profile'))

    def is_player (self):
        return True

    def is_club (self):
        return False


class ClubProfile (UserProfile):
    """
    Holds extra data about the registered club.-
    """
    address = models.CharField (max_length=200,
                                verbose_name=_('Address'))
    city = models.ForeignKey (City,
                              verbose_name=City._meta.verbose_name)
    phone = models.CharField (max_length=50,
                              verbose_name=_('Telephone numbers'))
    company = models.CharField (max_length=200,
                                verbose_name=_('Club or company name'))
    representative = models.CharField (max_length=100,
                                       default='-',
                                       verbose_name=_("Representative's full name"))
    representative_title = models.CharField (max_length=50,
                                             default='-',
                                             verbose_name=_("Representative's title"))
    tax_number = models.CharField (max_length=50,
                                   default='-',
                                   verbose_name=_('Tax number'))

    def clean (self):
        """
        Don't allow a club to have a player profile.-
        """
        if PlayerProfile.objects.filter (user=self.user):
            raise ValidationError (_('This user has already been assigned a player profile'))

    def is_player (self):
        return False

    def is_club (self):
        return True


@receiver (post_save, sender=ClubProfile, dispatch_uid="club_profile_post_save")
def club_profile_handler (sender, instance, created, **kwargs):
    """
    Callback function used whenever a club's profile is created or
    updated. It generates a user's action in the 'activity' app.-
    """
    if created:
        action.send (instance.user, verb='created', target=instance)
    else:
        action.send (instance.user, verb='updated', target=instance)



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
    prof = UserProfile.objects.get_profile (instance.username)
    if prof:
        if prof.is_player ( ):
            PlayerProfile.objects.get (pk=prof.id).delete ( )
        if prof.is_club ( ):
            ClubProfile.objects.get (pk=prof.id).delete ( )
        action.send (instance, verb='deleted', target=prof)

