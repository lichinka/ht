from abc import abstractmethod

from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_delete
from django.contrib.auth.models import User

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
        Associates a player profile to the received user.-
        """
        if self.get_profile (username) is None:
            u = User.objects.get (username=username)
            pp = PlayerProfile.objects.create (level='B',
                                               user=u)
            return pp
        else:
            return None


    def create_club_profile (self, username, address, city, phone, company):
        """
        Associates a club profile to the received user.-
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
            return None


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
        return self.user.username


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
    address = models.CharField (max_length=200)
    city = models.ForeignKey (City)
    phone = models.CharField (max_length=50,
                              null=False,
                              blank=False)
    company = models.CharField (max_length=200,
                                null=False,
                                blank=False)

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


@receiver(pre_delete, sender=User)
def delete_associated_profile (sender, instance, **kwargs):
    """
    Callback function used whenever a user is to be
    deleted. It deletes the associated Player/Club Profile.-
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

