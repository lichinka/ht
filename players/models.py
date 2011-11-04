from accounts.models import PlayerProfile
from locations.models import City

from django.db import models
from django.utils.translation import ugettext_lazy as _

        

class Vacancy (models.Model):
    """
    Defines a time and place interval for a player to play.-
    """
    DAYS=(('WD', _('Week days')),
          ('WN', _('Weekends')),
          ('SA', _('Saturdays')),
          ('SU', _('Sundays')),
          ('MO', _('Mondays')),
          ('TU', _('Tuesdays')),
          ('WE', _('Wednesdays')),
          ('TH', _('Thursdays')),
          ('FR', _('Fridays')))
    FROM_TO=(('F', _('from')),
             ('T', _('up to')))
    HOURS=(('07', '7:00'),
           ('08', '8:00'),
           ('09', '9:00'),
           ('10', '10:00'),
           ('11', '11:00'),
           ('12', '12:00'),
           ('13', '13:00'),
           ('14', '14:00'),
           ('15', '15:00'),
           ('16', '16:00'),
           ('17', '17:00'),
           ('18', '18:00'),
           ('19', '19:00'),
           ('20', '20:00'),
           ('21', '21:00'),
           ('22', '22:00'),
           ('23', '23:00'))
    player = models.ForeignKey (PlayerProfile,
                                null=False,
                                blank=False)
    day = models.CharField (max_length=2,
                            choices=DAYS,
                            default='WN',
                            null=False,
                            blank=False)
    from_to = models.CharField (max_length=1,
                                choices=FROM_TO,
                                default='F',
                                null=False,
                                blank=False)
    hour = models.CharField (max_length=2,
                             choices=HOURS,
                             default='07',
                             null=False,
                             blank=False)
    city = models.ForeignKey (City,
                              null=False,
                              blank=False)

    @staticmethod
    def get_weekdays ( ):
        """
        Returns a list with the week days.-
        """
        ret_value = [Vacancy.DAYS[4][0],
                     Vacancy.DAYS[5][0],
                     Vacancy.DAYS[6][0],
                     Vacancy.DAYS[7][0],
                     Vacancy.DAYS[8][0]]
        return ret_value
    
    
    @staticmethod
    def get_weekends ( ):
        """
        Returns a list with the weekend days.-
        """
        ret_value = list ( )
        ret_value.append (Vacancy.DAYS[2][0])
        ret_value.append (Vacancy.DAYS[3][0])
        return ret_value
    