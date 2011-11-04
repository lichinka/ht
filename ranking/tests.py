from datetime import datetime

from django.test import TestCase
from django.contrib.auth.models import User

from ranking.models import Result, SingleMatch, Ranking
from accounts.models import UserProfile
from locations.models import City



class ResultTest (TestCase):
    """
    All tests regarding the Result model.
    """
    def test_get_sets (self):
        """
        Checks that the entered results are correctly parsed.-
        """
        err_msg = "Function 'Result.get_sets' returned incorrect results."
        r0 = Result.objects.create (type=1,
                                    score='10:8')
        self.assertTrue(r0.get_sets ( ) == ['10:8'], err_msg)
        r1 = Result.objects.create (type=3,
                                    score='6:3,4:6,6:1')
        self.assertTrue(r1.get_sets ( ) == ['6:3','4:6','6:1'], err_msg)
        r2 = Result.objects.create (type=3,
                                    score='6:3,7:5')
        self.assertTrue(r2.get_sets ( ) == ['6:3', '7:5'], err_msg)
        r3 = Result.objects.create (type=5,
                                    score='6:1,6:2,6:4')
        self.assertTrue(r3.get_sets ( ) == ['6:1', '6:2', '6:4'], err_msg)
        r4 = Result.objects.create (type=5,
                                    score='6:7,5:7,6:3,6:2,6:4')
        self.assertTrue(r4.get_sets ( ) == ['6:7', '5:7', '6:3', '6:2', '6:4'], err_msg)
        r5 = Result.objects.create (type=5,
                                    score='6:1,5:7,6:3,7:5')
        self.assertTrue(r5.get_sets ( ) == ['6:1', '5:7', '6:3', '7:5'], err_msg)
    
    
    
class RankingTest (TestCase):
    """
    All tests regarding the Ranking model.-
    """
    def setUp (self):
        """
        Creates some test matches used during testing.-
        """
        u  = User.objects.create_user ('winner_player', 'winner@nowhere.si', 'pass')
        wp = UserProfile.objects.create_player_profile (u)
        u  = User.objects.create_user ('loser_player', 'loser@nowhere.si', 'pass')
        lp = UserProfile.objects.create_player_profile (u)
        r = Result.objects.create (type=3,
                                   score='6:3,7:5') 
        SingleMatch.objects.create (winner = wp,
                                    loser = lp,
                                    result = r,
                                    date = datetime.now ( ),
                                    city = City.objects.all ( )[0])
        
    def test_ranking_points (self):
        """
        Checks that each player has the correct number of points.-
        """
        p = UserProfile.objects.get_profile ('winner_player')
        r = Ranking.objects.get (player=p)
        self.assertTrue (r.points == 13,
                         "Incorrect number of points in ranking for player '%s'" % p.user.username)
         
        p = UserProfile.objects.get_profile ('loser_player')
        r = Ranking.objects.get (player=p)
        self.assertTrue (r.points == 8,
                         "Incorrect number of points in ranking for player '%s'" % p.user.username)
    
    def test_ranking_points_after_another_match (self):
        """
        Checks that each player has the correct number of points.-
        """
        wp = UserProfile.objects.get_profile ('winner_player')
        lp = UserProfile.objects.get_profile ('loser_player')
        SingleMatch.objects.create (winner = lp,
                                    loser = wp,
                                    result = Result.objects.create (type=3,
                                                                    score='6:1,5:7,7:5'),
                                    date = datetime.now ( ),
                                    city = City.objects.all ( )[1])
        
        r = Ranking.objects.get (player=wp)
        self.assertTrue (r.points == 26,
                         "Incorrect number of points in ranking for player '%s' (%s)" % (wp.user.username,
                                                                                         str(r.points)))
        r = Ranking.objects.get (player=lp)
        self.assertTrue (r.points == 26,
                         "Incorrect number of points in ranking for player '%s' (%s)" % (lp.user.username,
                                                                                         str(r.points)))
        