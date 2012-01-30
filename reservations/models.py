from datetime import datetime, timedelta

from django.db import models
from django.dispatch import receiver
from django.db.models import Count, Max
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from actstream import action
from clubs.models import Vacancy
from django.core.exceptions import FieldError
from accounts.models import UserProfile



class ReservationMixin (object):
    """
    Allows method chaining at manager level.-
    """
    def by_court_setup (self, cs):
        """
        Returns a query set containing all reservations of all
        courts of the received court setup.
        WARNING: reservations of inactive courts are also returned.-
        """
        return self.filter (vacancy__court__court_setup=cs)

    def by_date (self, cs, for_date):
        """
        Returns a query set containing all reservations
        for the given date and court setup.
        WARNING: reservations of inactive courts are also returned.-
        """
        return self.by_court_setup (cs).filter (for_date=for_date)

    def from_date (self, cs, from_date):
        """
        Returns a query set containing all reservations
        starting from (and including) the given date.
        WARNING: reservations of inactive courts are also returned.-
        """
        return self.by_court_setup (cs).filter (for_date__gte=from_date)

    def up_to_date (self, cs, until_date):
        """
        Returns a query set containing all reservations
        up to (but NOT including) the given date.
        WARNING: reservations of inactive courts are also returned.-
        """
        return self.by_court_setup (cs).filter (for_date__lt=until_date)


class ReservationQuerySet (QuerySet, ReservationMixin):
    """
    Glue class to build a manager that supports method chaining.-
    """
    pass


class ReservationManager (models.Manager, ReservationMixin):
    """
    A tuned manager that supports method chaining.-
    """
    def get_query_set (self):
        return ReservationQuerySet (self.model, using=self._db)

    def book (self, commit=True, **kwargs):
        """
        Creates a reservation by booking a free vacancy term.
        It returns the reservation created or None if something went wrong.-
        """
        ret_value = None
        #
        # the target vacancy term should be free
        #
        book_count = Reservation.objects.filter (for_date=kwargs['for_date']) \
                                        .filter (vacancy=kwargs['vacancy']) \
                                        .aggregate (Count ('id'))
        if int(book_count['id__count']) < 1:
            #
            # the target court should be available
            #
            if kwargs['vacancy'].court.is_available:
                #
                # get the user profile
                #
                usr_profile = UserProfile.objects.get_profile (kwargs['user'].username)
                if usr_profile.is_player ( ):
                    kwargs['type'] = 'P'
                elif usr_profile.is_club ( ):
                    kwargs['type']  = 'C'
                else:
                    return ret_value
                #
                # if description is empty, or it has not been given,
                # save the user name
                #
                try:
                    kwargs['description'] = kwargs['description'].strip ( )
                except KeyError:
                    kwargs['description'] = ''
                if len (kwargs['description']) == 0:
                    kwargs['description'] = '%s %s' % (kwargs['user'].first_name,
                                                       kwargs['user'].last_name)
                #
                # create the new reservation
                #
                r = Reservation (**kwargs)
                if commit:
                    r.save ( )
                    ret_value = Reservation.objects.get (pk=r.id)
                else:
                    ret_value = r
        return ret_value


    def book_weekly (self, from_date, until_date, commit=True, **kwargs):
        """
        Creates weekly reservations, starting from 'from_date'.
        It returns a list containing the reservations created.-
        """
        ret_value = []
        #
        # end date should be later than start date
        #
        if until_date > from_date:
            #
            # dates for the reservations that should be created
            #
            series_dates = [from_date]
            while until_date > series_dates[-1]:
                next_date = series_dates[-1] + timedelta (days=7)
                series_dates.append (next_date)
            if series_dates[-1] > until_date:
                series_dates.pop ( )
            #
            # create one reservation for each date in the series,
            # all with the same repeating-series identifier
            #
            repeat_series_id = Reservation.objects.get_next_repeat_series ( )
            for d in series_dates:
                new_r = Reservation.objects.book (for_date=d,
                                                  repeat_series=repeat_series_id,
                                                  commit=commit,
                                                  **kwargs)
                if new_r is not None:
                    ret_value.append (new_r)
        return ret_value


    def get_weekly_reservation_count (self, from_date, until_date):
        """
        Returns the number of weekly reservations, starting
        (and including) 'from_date', and ending with 'until_date'.-
        """
        ret_value = 0
        if until_date > from_date:
            ret_value = (until_date - from_date).days
            ret_value += 7 - (ret_value % 7)
            ret_value /= 7
        return ret_value


    def get_next_repeat_series (self):
        """
        Returns an integer that can be safely used as a series
        identifier for repeating reservations.-
        """
        ret_value = Reservation.objects.exclude (repeat_series__isnull=True) \
                                       .aggregate (Max ('repeat_series'))
        if ret_value['repeat_series__max']:
            ret_value = int (ret_value['repeat_series__max']) + 1
        else:
            ret_value = 1
        return ret_value


    def copy_to_court_setup (self, target_cs, reservation_list, commit=True):
        """
        Copies the received reservations to the target court setup. It
        returns a list with the target reservations that were successfully
        copied. If the 'commit' parameter is False, no new reservations are
        actually created in the DB.
        WARNING: all repeating reservations are given a new
                 repeat_series identifier!
        """
        source_cs = reservation_list[0].vacancy.court.court_setup
        #
        # newly generated series identifiers for repeating reservations
        #
        new_series = dict ( )
        #
        # source and target court setups should not be the same object
        #
        if source_cs != target_cs:
            copied = list ( )
            for r in reservation_list:
                #
                # all reservations must belong to the same source court setup
                #
                if r.vacancy.court.court_setup == source_cs:
                    #
                    # give a new repeat_series identifier if this
                    # reservation is part of one
                    #
                    if r.repeat_series is not None:
                        if r.repeat_series not in new_series.keys ( ):
                            new_series[r.repeat_series] = Reservation.objects.get_next_repeat_series ( )
                        tgt_repeat_series = new_series[r.repeat_series]
                    else:
                        tgt_repeat_series = None
                    #
                    # prefer copying the reservation to the same court
                    # in the target court setup
                    #
                    free_tgt_terms = Vacancy.objects.get_free (target_cs,
                                                               r.for_date,
                                                               r.vacancy.available_from)
                    free_tgt_terms = free_tgt_terms.filter (court__number=r.vacancy.court.number)
                    if free_tgt_terms:
                        #
                        # copy the reservation here
                        #
                        tgt_r = Reservation.objects.book (created_on=r.created_on,
                                                          for_date=r.for_date,
                                                          vacancy=free_tgt_terms[0],
                                                          user=r.user,
                                                          description=r.description,
                                                          repeat_series=tgt_repeat_series,
                                                          commit=commit)
                        if tgt_r is not None:
                            copied.append (tgt_r)
                    else:
                        #
                        # try to accommodate the current reservation in any
                        # of the free vacancy terms of the target court setup
                        #
                        free_tgt_terms = Vacancy.objects.get_free (target_cs,
                                                                   r.for_date,
                                                                   r.vacancy.available_from)
                        for tgt_v in free_tgt_terms.iterator ( ):
                            tgt_r = Reservation.objects.book (created_on=r.created_on,
                                                              for_date=r.for_date,
                                                              vacancy=tgt_v,
                                                              user=r.user,
                                                              description=r.description,
                                                              repeat_series=tgt_repeat_series,
                                                              commit=commit)
                            if tgt_r is not None:
                                copied.append (tgt_r)
                                break
                else:
                    raise FieldError ("Not all reservations belong to the same court setup")
        else:
            raise FieldError ("Source and target court setups are the same")
        return copied


    def delete (self, r):
        """
        Deletes the received reservation object, or the whole
        series if it is part of a repetition one.-
        """
        if r.repeat_series is None:
            r.delete ( )
        else:
            Reservation.objects.filter (repeat_series=r.repeat_series) \
                               .delete ( )

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
    TYPES = (('P', _('By player')),
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


@receiver (post_save, sender=Reservation)
def reservation_handler (sender, instance, created, raw, **kwargs):
    """
    Callback function used whenever a reservation is created, updated
    or deleted. It generates a user's action.-
    """
    #
    # Make sure a new reservation has been created by hand
    #
    if created and not raw:
        action.send (instance.user, verb='created', target=instance)
    elif not created:
        #
        # A reservation has been updated
        #
        action.send (instance.user, verb='updated', target=instance)

