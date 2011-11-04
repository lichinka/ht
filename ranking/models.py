import re

from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from locations.models import City
from accounts.models import PlayerProfile




class Result (models.Model):
    """
    Represents the result of a tennis match. There are three
    types of them, and the scores are kept in a comma-separated
    CharField, with a colon between the number of games for each
    player (winner is always first), e.g.:
   
        type=1
        score="10:8"
        
        type=3
        score="6:3,4:6,6:1"
        
        type=5
        score="6:1,6:2,6:4"
        
    """
    GAMES_DELIMITER=':'
    SETS_DELIMITER='[\s,.-]'
    TYPES=((1, _('One set')),
           (3, _('Best of three sets')),
           (5, _('Best of five sets')))
    type = models.PositiveSmallIntegerField (choices=TYPES,
                                             default=1)
    score = models.CharField (max_length=30)
    
    def get_sets (self):
        """
        Returns a list of results per set, e.g.
        
            '6:3,7:6'
            get_sets ( ) -> ['6:3','7:6']
        """
        return re.split ('%s*' % Result.SETS_DELIMITER,
                         self.score)
    
    def __unicode__ (self):
        return self.score
    

class SingleMatchManager (models.Manager):
    def get_winner_results (self, player):
        """
        Returns a QuerySet with all the matches the player won
        and their results.-
        """
        ret_value = SingleMatch.objects.filter (is_challenged=False) \
                                       .filter (winner=player)
        return ret_value
    
    def get_loser_results (self, player):
        """
        Returns a QuerySet with all the matches the user lost
        and their results.-
        """
        ret_value = SingleMatch.objects.filter (is_challenged=False) \
                                       .filter (loser=player)
        return ret_value
    
    def get_results (self, user):
        """
        Returns a QuerySet with all the matches and their results
        for the user 'user'.-
        """
        if PlayerProfile.objects.filter (user=user):
            player = PlayerProfile.objects.get (user=user)
            ret_value  = SingleMatch.objects.get_winner_results (player)
            ret_value |= SingleMatch.objects.get_loser_results (player)
        else:
            ret_value = SingleMatch.objects.none ( )
        return ret_value



class SingleMatch (models.Model):
    """
    Represents a match between two players.-
    """
    winner = models.ForeignKey (PlayerProfile,
                                related_name='winner')
    loser = models.ForeignKey (PlayerProfile,
                               related_name='loser')
    result = models.ForeignKey (Result,
                                unique=True)
    date = models.DateField (null=True,
                             blank=True)
    city = models.ForeignKey (City,
                              null=True,
                              blank=True)
    is_challenged = models.BooleanField (default=False)
    objects = SingleMatchManager ( )
       
    def __unicode__ (self):
        return '%s %s %s %s' % (self.winner.user.username,
                               _('won'),
                               self.loser.user.username,
                               self.result)



class Ranking (models.Model):
    """
    Represents the players' ranking.-
    """
    player = models.ForeignKey (PlayerProfile,
                                unique=True)
    points = models.PositiveIntegerField (default = 0)
    
    def __unicode__ (self):
        return "%s %s" % (self.player.user_profile.user.username,
                          self.points)



@receiver(post_save, sender=SingleMatch)
def calculate_ranking (sender, instance, created, **kwargs):
    """
    Callback function called whenever a new match result is created.
    It (re)calculates the points earned by each player who has entered
    any match results.-
    """
    #
    # Make sure a new match results has been inserted
    #
    if (created):
        #
        # recalculate points for theses players
        #
        players = [instance.winner,
                   instance.loser]
        for p in players:
            points = 0
            matches = SingleMatch.objects.get_winner_results (p)
           
            for m in matches:
                for s in m.result.get_sets ( ):
                    points += int (re.split (Result.GAMES_DELIMITER, s)[0])
            #
            # recalculate points for the matches lost
            #
            matches = SingleMatch.objects.get_loser_results (p)
           
            for m in matches:
                for s in m.result.get_sets ( ):
                    points += int (re.split (Result.GAMES_DELIMITER, s)[1])
            #
            # Try to find a ranking entry for this player
            #
            r = Ranking.objects.filter (player=p)
            if not r:
                r = Ranking ( )
                r.player = p
            else:
                r = r[0]
            r.points = points
            r.save ( )
        