from django.test import TestCase
from django.contrib.auth.models import User

from accounts.models import UserProfile, ClubProfile, PlayerProfile
from locations.models import City




class UserProfileTest (TestCase):
    """
    All tests regarding the UserProfile model.
    """
    def setUp (self):
        """
        Creates some test players and clubs used during testing.-
        """
        p = User.objects.create_user ('test_player', 'player@nowhere.si', 'pass')
        UserProfile.objects.create_player_profile (p)
        c = User.objects.create_user ('test_club', 'club@nowhere.si', 'pass')
        UserProfile.objects.create_club_profile (c,
                                                 "Postal address 1231",
                                                 City.objects.all ( )[0],
                                                 "111-222-333",
                                                 "The best tennis club d.o.o.")


    def test_player_cannot_be_club (self):
        """
        Checks that a player cannot have a club's profile associated.-
        """
        pp = UserProfile.objects.get_profile ('test_player')
        cp = UserProfile.objects.create_club_profile (pp.user.username,
                                                      "Some address",
                                                      City.objects.all ( )[0],
                                                      "Some phone",
                                                      "Some company")
        self.assertTrue (cp is None,
                         "A club's profile has been associated with an existing player")
        self.assertTrue (len (ClubProfile.objects.filter (user__username='test_player')) == 0,
                         "A club's profile has been associated with an existing player")


    def test_player_profile_creation (self):
        """
        Checks that the player profile is correctly created.-
        """
        up = UserProfile.objects.get_profile ('test_player')

        self.assertTrue (up.is_player ( ),
                         "The created player's profile is incorrect")
        self.assertTrue (up.is_club ( ) == False,
                         "The created player's profile is incorrect")
        self.assertTrue (up.level == 'B')
        self.assertTrue (up.male)
        self.assertTrue (up.right_handed)


    def test_player_profile_deletion (self):
        """
        Checks that the corresponding profile is deleted with the user.-
        """
        u = User.objects.get (username='test_player')
        up = UserProfile.objects.get_profile (u.username)
        u.delete ( )
        self.assertTrue (len (PlayerProfile.objects.filter (pk=up.id)) == 0,
                         "The related player's profile has not been deleted")


    def test_club_profile_creation (self):
        """
        Checks that the club profile is correctly created.-
        """
        up = UserProfile.objects.get_profile ('test_club')

        self.assertTrue (up.is_club ( ),
                         "The created club's profile is incorrect")
        self.assertTrue (up.is_player ( ) == False,
                         "The created club's profile is incorrect")
        self.assertTrue (up.address == 'Postal address 1231')
        self.assertTrue (up.city == City.objects.all ( )[0])
        self.assertTrue (up.phone == '111-222-333')
        self.assertTrue (up.company == 'The best tennis club d.o.o.')


    def test_club_profile_deletion (self):
        """
        Checks that the corresponding profile is deleted with the user.-
        """
        u = User.objects.get (username='test_club')
        up = UserProfile.objects.get_profile (u.username)
        u.delete ( )
        self.assertTrue (len (ClubProfile.objects.filter (pk=up.id)) == 0,
                         "The related club's profile has not been deleted")

