from django.db import models, transaction
from django.dispatch import receiver
from django.db.models import Count, Max
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, pre_delete
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.db.models.deletion import ProtectedError

from ht_utils import update_many, insert_many
from accounts.models import ClubProfile



class CourtSetupManager (models.Manager):
    def get_active (self, club):
        """
        Returns the currently active court setup or None.-
        """
        try:
            cid = club['id']
        except TypeError:
            #
            # club is an object
            #
            cid = club.id
        cs = CourtSetup.objects.filter (club__id=cid) \
                               .filter (is_active=True)
        cs = cs[0] if cs else None
        return cs
    
    
    def get_count (self, club):
        """
        Returns the number of court setups contained in the
        received 'club'.-
        """
        count = CourtSetup.objects.filter (club=club) \
                                  .aggregate (Count ('id'))
        return int (count['id__count'])
    
   
    @transaction.commit_on_success
    def activate (self, court_setup):
        """
        Marks the received court setup as active, deactivating
        all others, as there always should be strictly one
        active court setup.-
        """
        #
        # deactivate all court setups owned by the same club
        #
        for cs in CourtSetup.objects.filter (club=court_setup.club).iterator ( ):
            cs.is_active = False
            cs.save ( )
        #
        # activate the received court setup
        #
        court_setup.is_active = True
        court_setup.save ( )
            
    
    @transaction.commit_on_success
    def delete (self, court_setup, force=False):
        """
        Deletes the received court setup, including all its
        referenced objects. If there are reservations attached 
        to it, the court setup (and its reservations) are deleted
        only if the 'force' flag is True.-
        """
        from reservations.models import Reservation
        #
        # do not allow the deletion of the last court setup of a club
        #
        if self.get_count (court_setup.club) > 1:
            #
            # do not allow the deletion of this court setup
            # if it has any reservations attached to itself
            #
            res_count = Reservation.objects.by_court_setup (court_setup) \
                                           .aggregate (Count ('id'))
            if (res_count['id__count'] == 0) or force:
                #
                # delete all reservations from all
                # courts of the received court setup
                #
                for court in Court.objects.filter (court_setup=court_setup):
                    Court.objects.delete_reservations (court)
                court_setup.delete ( )
                #
                # activate another court setup
                #
                cs = CourtSetup.objects.filter (club=court_setup.club).values ('id')
                cs = CourtSetup.objects.get (pk=cs[0]['id'])
                CourtSetup.objects.activate (cs)
            
            
    @transaction.commit_on_success
    def clone (self, court_setup):
        """
        Clones a court setup of a club, including all its courts, 
        their properties and vacancy terms. Returns the newly created
        court setup.-
        """
        clone_name = "%s %s" % (ugettext('Copy of'), court_setup.name)
        clone = self.model.objects.create (name=clone_name,
                                           club=court_setup.club,
                                           is_active=False)
        #
        # delete any existing courts in the cloned court setup,
        # that may have been created by callback functions
        #
        Court.objects.filter (court_setup=clone).delete ( )
        #
        # clone all courts contained in this court setup
        #
        for court in Court.objects.filter (court_setup=court_setup):
            cloned_court = Court.objects.clone (court)
            cloned_court.court_setup = clone
            cloned_court.number = court.number
            cloned_court.save ( )
        return clone
    
    
    
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
        
        
            
class CourtManager (models.Manager):
    def delete_reservations (self, court):
        """
        Deletes all reservations attached to the received court.-
        """
        from reservations.models import Reservation
        for r in Reservation.objects.filter (vacancy__court=court).iterator ( ):
            Reservation.objects.delete (r)
            
        
    def get_available (self, court_setup):
        """
        Returns a query set of available courts belonging
        to the received 'court_setup'.-
        """
        courts = Court.objects.filter (court_setup=court_setup) \
                              .filter (is_available=True)
        return courts
    
    
    def get_count (self, court_setup):
        """
        Returns the number of courts contained
        in the received 'court_setup'.-
        """
        count = Court.objects.filter (court_setup=court_setup) \
                             .aggregate (Count ('id'))
        return int(count['id__count'])
    
    
    def clone (self, court):
        """
        Clones a court within a court setup, including all its 
        properties and vacancy terms. Returns the newly created
        court.-
        """
        clone_num = self.model.objects.aggregate (Max ('number'))
        clone_num = clone_num['number__max'] + 1
        clone = self.model.objects.create (court_setup=court.court_setup,
                                           number=clone_num,
                                           indoor=court.indoor,
                                           light=court.light,
                                           surface=court.surface,
                                           single_only=court.single_only,
                                           is_available=court.is_available)
        #
        # copy active vacancy terms to the cloned court
        #
        bulk = []
        v_terms = Vacancy.objects.filter (court=court) \
                                 .filter (price__isnull=False)
        for v in v_terms:
            c_v = Vacancy.objects.filter (court=clone,
                                          day_of_week=v.day_of_week,
                                          available_from=v.available_from,
                                          available_to=v.available_to)
            if c_v:
                c_v = c_v[0]
                c_v.price = v.price
                bulk.append (c_v)
        #
        # update the copied vacancy prices
        #
        update_many (bulk, fields=['price'])
        return clone
 
 
 
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
            


class VacancyMixin (object):
    """
    Allows method chaining at manager level.-
    """
    def get_free (self, cs, for_date, hour):
        """
        Returns a query set of free vacancies (i.e. not yet booked) for
        the given date and hour, for active courts belonging to the given
        court setup.-
        """
        from reservations.models import Reservation
        
        booked = Reservation.objects.by_date (cs, for_date) \
                                    .filter (vacancy__available_from=hour) \
                                    .values ('vacancy__id')
        return self.filter (court__court_setup=cs) \
                   .filter (day_of_week=for_date.isoweekday ( )) \
                   .filter (available_from=hour) \
                   .exclude (court__is_available=False) \
                   .exclude (id__in=booked)
        
        
    def get_all (self, courts=None, day_of_week_list=None, hour_list=None):
        """
        Returns a query set of all vacancies, optionally filtering by the
        object lists received.-
        """
        v = self.all ( )
        
        if courts:
            try:
                #
                # correctly handle a list of dictionaries
                # (as returned by qset.values ( ))
                #
                court_list = [c['id'] for c in courts if 'id' in c.keys ( )]
            except AttributeError:
                #
                # correctly handle lists of objects, ids and query sets
                #
                court_list = [c for c in courts]
            v = v.filter (court__in=court_list)
        if day_of_week_list:
            v = v.filter (day_of_week__in=day_of_week_list)
        if hour_list:
            v = v.filter (available_from__in=hour_list)
        return v


    def get_all_by_date (self, courts=None, date_list=None, hour_list=None):
        """
        Returns a query set of all vacancies, optionally filtering by the
        object lists received.-
        """
        if date_list:
            dow_list = [d.isoweekday ( ) for d in date_list]
        return self.get_all (courts, dow_list, hour_list)


class VacancyQuerySet (QuerySet, VacancyMixin):
    """
    Glue class to build a manager that supports method chaining.-
    """
    pass


class VacancyManager (models.Manager, VacancyMixin):
    """
    A tuned manager that supports method chaining.-
    """
    def get_query_set (self):
        return VacancyQuerySet (self.model, using=self._db)
    

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
