from django.db import models
from django.dispatch import receiver
from django.db.models import Count, Max
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from clubs.managers import CourtManager, CourtSetupManager, VacancyManager
from accounts.models import ClubProfile



class CourtSetup (models.Model):
    """
    Enables different court configurations per club.-
    """
    name = models.CharField (max_length=100)
    club = models.ForeignKey (ClubProfile)
    is_active = models.BooleanField (default=False)
    objects = CourtSetupManager ( )

    def clean (self):
        """
        Only one court setup per club should be active.-
        """
        count = CourtSetup.objects.filter (club=self.club) \
                                  .filter (is_active=True)
        count = count.exclude (id=self.id) if self.id else count
        count = count.aggregate (Count ('id'))
        if (count['id__count'] > 0) and (self.is_active):
            raise ValidationError (_('Only one court setup may be active at once'))
    
    def __unicode__ (self):
        return self.name
    


@receiver (post_save, sender=ClubProfile)
def create_courtsetup (sender, instance, created, raw, **kwargs):
    """
    Callback function used whenever a new club profile is created.
    It creates a default court setup.-
    """
    #
    # Make sure a new club profile has been created by hand
    # (i.e. without fixtures)
    #
    if created and not raw:
        cs = CourtSetup.objects.create (name=ugettext('Default'),
                                        club=instance,
                                        is_active=True)
        cs.save ( )
        
        
            
class Court (models.Model):
    """
    A club's tennis court that is available for reservation.-
    """
    SURFACES = (('CL', _('Clay')),
                ('CE', _('Cement')),
                ('GR', _('Grass')),
                ('RU', _('Rubber')),
                ('CA', _('Carpet')))
    
    court_setup = models.ForeignKey (CourtSetup)
    number = models.IntegerField ( )
    indoor = models.BooleanField (default=False)
    light = models.BooleanField (default=True)
    surface = models.CharField (max_length=2,
                                choices=SURFACES,
                                default='CL')
    single_only = models.BooleanField (default=False)
    is_available = models.BooleanField (default=True)
    objects = CourtManager ( )
   
    class Meta:
        #
        # Don't allow a club to have repeated 
        # court numbers within an active setup
        # 
        unique_together = ('court_setup', 'number')
    
    def get_club (self):
        """
        Returns the club of this court.-
        """
        return self.court_setup.club
    
    def __unicode__ (self):
        return str (self.number)
 

 
@receiver (post_save, sender=CourtSetup)
def create_court (sender, instance, created, raw, **kwargs):
    """
    Callback function used whenever a new court setup is created.
    It creates one default court.-
    """
    #
    # Make sure a new court setup has been created by hand
    # (i.e. without fixtures)
    #
    if created and not raw:
        #
        # ... and that there are no courts yet
        #
        if Court.objects.get_count (instance) < 1:
            next_num = Court.objects.filter (court_setup=instance) \
                                    .aggregate (Max ('number'))
            if next_num['number__max']:
                next_num = next_num['number__max'] + 1
            else:
                next_num = 1
            c = Court.objects.create (court_setup=instance,
                                      number=next_num)
            c.save ( )



class Vacancy (models.Model):
    """
    Defines when and for how much a court is available for reservation.-
    """
    DAYS=((1, _('Monday')),
          (2, _('Tuesday')),
          (3, _('Wednesday')),
          (4, _('Thursday')),
          (5, _('Friday')),
          (6, _('Saturday')),
          (7, _('Sunday')))
    HOURS=((7, '7:00'),
           (8, '8:00'),
           (9, '9:00'),
           (10, '10:00'),
           (11, '11:00'),
           (12, '12:00'),
           (13, '13:00'),
           (14, '14:00'),
           (15, '15:00'),
           (16, '16:00'),
           (17, '17:00'),
           (18, '18:00'),
           (19, '19:00'),
           (20, '20:00'),
           (21, '21:00'),
           (22, '22:00'),
           (23, '23:00'),
           (24, '24:00'))
   
    court = models.ForeignKey (Court)
    day_of_week = models.IntegerField (choices=DAYS,
                                       default=1)
    available_from = models.IntegerField (choices=HOURS,
                                          default=8)
    available_to = models.IntegerField (choices=HOURS,
                                        default=9)
    price = models.DecimalField (max_digits=5,
                                 decimal_places=2,
                                 null=True,
                                 blank=True)
    objects = VacancyManager ( )
    
    class Meta:
        #
        # Don't allow court vacancies to overlap
        # 
        unique_together = ('court',
                           'day_of_week',
                           'available_from', 
                           'available_to')
        
    def clean (self):
        """
        Vacancy terms should be exactly one hour long.-
        """
        if (self.available_to - self.available_from) != 1:
            raise ValidationError (_('Vacancy terms should be one hour long'))
        
    def __unicode__ (self):
        return "%s, %s %s %s %s" % (self.get_day_of_week_display ( ),
                                    _('from'),
                                    self.available_from,
                                    _('to'),
                                    self.available_to)



@receiver (post_save, sender=Court)
def create_court_vacancy_terms (sender, instance, created, raw, **kwargs):
    """
    Callback function used whenever a new court is created.
    It creates all possible Vacancy terms for it.-
    """
    from ht_utils.models import insert_many
    #
    # Make sure a new court has been created by hand
    # (i.e. without fixtures)
    #
    if created and not raw:
        bulk = []
        days = [k for k,e in Vacancy.DAYS]
        hours = [k for k,e in Vacancy.HOURS]
        for d in days:
            for h in hours[:-1]:
                v = Vacancy (court=instance,
                             day_of_week=d,
                             available_from=h,
                             available_to=h+1,
                             price=None)
                bulk.append (v)
        insert_many (bulk)
 
 

@receiver(pre_delete, sender=Court)
def delete_associated_vacancy_terms (sender, instance, **kwargs):
    """
    Callback function used whenever a court is to be
    deleted. It deletes the associated Vacancy terms.-
    """
    #
    # Delete all Vacancy terms associated with this Court
    #
    Vacancy.objects.filter (court=instance).delete ( )
