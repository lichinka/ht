from datetime import datetime, timedelta

from django.db import models
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from clubs.models import Vacancy



class ReservationManager (models.Manager):
    def get_by_date (self, for_date):
        """
        Returns a query set containing all reservations 
        for the given date.-
        """
        return Reservation.objects.filter (for_date=for_date)
        
    def get_count_for_today (self):
        """
        Returns the number of reservations for today.-
        """
        today = datetime.today ( )
        count = Reservation.objects.filter (for_date=today) \
                                   .aggregate (Count ('id'))
        return int(count['id__count'])
        
    def get_count_for_tomorrow (self):
        """
        Returns the number of reservations for tomorrow.-
        """
        one_day = timedelta (days=1)
        tomorrow = datetime.today ( )+ one_day
        count = Reservation.objects.filter (for_date=tomorrow) \
                                   .aggregate (Count ('id'))
        return int(count['id__count'])
    
    def get_count_for_week (self):
        """
        Returns the number of reservations for next week.-
        """
        today = datetime.today ( )
        one_week = timedelta (weeks=1)
        next_week = today + one_week
        count = Reservation.objects.filter (for_date__range=(today, next_week)) \
                                   .aggregate (Count ('id'))
        return int(count['id__count'])
    
   
    
class Reservation (models.Model):
    """
    Represents a court reservation.-
    """
    TYPES=(('P', _('By player')),
           ('C', _('By club')),
           ('R', _('Repairs')))
    
    created_on = models.DateTimeField (default=datetime.now ( ))
    for_date = models.DateField ( )
    type = models.CharField (max_length=1,
                             choices=TYPES,
                             default='P')
    description = models.CharField (max_length=128,
                                    null=True,
                                    blank=True)
    user = models.ForeignKey (User)
    vacancy = models.ForeignKey (Vacancy,
                                 on_delete=models.PROTECT)
    repeat_series = models.IntegerField (null=True,
                                         blank=True)
    objects = ReservationManager ( )
   
    class Meta:
        #
        # don't allow the same vacancy term to be 
        # reserved twice within the same day 
        # 
        unique_together = ('for_date', 'vacancy')
    
    def __unicode__ (self):
        return "%s, %s: %s" % (self.created_on,
                               self.user.username,
                               self.vacancy)
        