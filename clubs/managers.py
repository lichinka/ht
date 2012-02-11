from django.db import models, transaction
from django.db.models import Count, Max
from django.db.models.query import QuerySet
from django.utils.translation import ugettext



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
        cs = self.filter (club__id=cid) \
                 .filter (is_active=True)
        cs = cs[0] if cs else None
        return cs
    
    
    def get_count (self, club):
        """
        Returns the number of court setups contained in the
        received 'club'.-
        """
        count = self.filter (club=club) \
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
        for cs in self.filter (club=court_setup.club).iterator ( ):
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
        from clubs.models import Court
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
                cs = self.filter (club=court_setup.club).values ('id')
                cs = self.get (pk=cs[0]['id'])
                self.activate (cs)
            
            
    @transaction.commit_on_success
    def clone (self, court_setup):
        """
        Clones a court setup of a club, including all its courts, 
        their properties and vacancy terms. Returns the newly created
        court setup.-
        """
        from clubs.models import Court
        #
        # put a new name together
        #
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
        courts = self.filter (court_setup=court_setup) \
                     .filter (is_available=True)
        return courts
    
    
    def get_count (self, court_setup):
        """
        Returns the number of courts contained
        in the received 'court_setup'.-
        """
        count = self.filter (court_setup=court_setup) \
                    .aggregate (Count ('id'))
        return int(count['id__count'])
    
    
    def clone (self, court):
        """
        Clones a court within a court setup, including all its properties
        and vacancy terms. Returns the newly created court.-
        """
        from ht_utils.models import update_many
        from clubs.models import Vacancy
        
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
    