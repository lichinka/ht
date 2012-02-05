import random
from datetime import date, timedelta

from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.deletion import ProtectedError
from django.db.models.aggregates import Count

from clubs.models import CourtSetup, Court, Vacancy
from reservations.models import Reservation
from ht_utils.tests.views import BaseViewTestCase



class ReservationTest (BaseViewTestCase):
    """
    All the test cases for the Reservation model.-
    """
    def test_manager_book_weekly (self):
        """
        Checks correct booking of weekly repeating terms.-
        """
        #
        # no reservations are booked if invalid dates are given
        #
        from_date = date.today ( ) + timedelta (days=random.randint (0, 10))
        until_date = from_date - timedelta (days=random.randint (5, 15))
        res_count = Reservation.objects.all ( ) \
                                       .aggregate (Count ('id'))
        # number of days between the two dates
        booking_count = abs ((until_date - from_date).days)
        # number of weekly reservations (i.e. every 7 days) 
        # starting (and including) 'from_date'
        booking_count += 7 - (booking_count % 7)
        booking_count /= 7
        booked = Reservation.objects.book_weekly (from_date, until_date)
        self.assertEquals (len(booked), 0)
        self.assertEquals (res_count,
                           Reservation.objects.all ( ).aggregate (Count ('id')))
        #
        # not all reservations are booked if any term is not free
        #
        res = random.choice (self.res_list)
        from_date = res.for_date
        v = res.vacancy
        until_date = from_date + timedelta (days=random.randint (5, 15))
        res_count = Reservation.objects.all ( ) \
                                       .aggregate (Count ('id'))
        # number of days between the two dates
        booking_count = (until_date - from_date).days
        self.assertFalse (booking_count < 0)
        # number of weekly reservations (i.e. every 7 days) 
        # starting (and including) 'from_date'
        booking_count += 7 - (booking_count % 7)
        booking_count /= 7
        booked = Reservation.objects.book_weekly (from_date, 
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  description="Weekly reservations",
                                                  commit=True)
        self.assertTrue (len(booked) < booking_count)
        self.assertEquals (res_count['id__count'] + len(booked),
                           Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'])
        #
        # correct booking in case of valid dates and free terms
        #
        cs = CourtSetup.objects.get_active (self.club)
        v = None
        while v is None:
            from_date = date.today ( ) + timedelta (days=random.randint (0, 10))
            v = Vacancy.objects.get_free (cs, from_date, Vacancy.HOURS[random.randint (0, 15)][0])
            v = v[0] if v else None
                
        until_date = from_date + timedelta (days=random.randint (5, 15))
        res_count = Reservation.objects.all ( ) \
                                       .aggregate (Count ('id'))
        # number of days between the two dates
        booking_count = (until_date - from_date).days
        self.assertFalse (booking_count < 0)
        # number of weekly reservations (i.e. every 7 days) 
        # starting (and including) 'from_date'
        booking_count += 7 - (booking_count % 7)
        booking_count /= 7
        #
        # if no commit, the record count on the DB should be unaltered
        #
        booked = Reservation.objects.book_weekly (from_date, 
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  description="Weekly reservations",
                                                  commit=False)
        self.assertEquals (len(booked), booking_count)
        self.assertEquals (res_count['id__count'],
                           Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'])
        #
        # if committing, the record count on the DB should grow
        #
        desc = "Weekly reservations"
        booked = Reservation.objects.book_weekly (from_date, 
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  description=desc,
                                                  commit=True)
        self.assertEquals (len(booked), booking_count)
        self.assertEquals (res_count['id__count'] + booking_count,
                           Reservation.objects.all ( ).aggregate (Count ('id'))['id__count'])
        #
        # the number of saved reservations with the
        # new series identifier should be correct
        # 
        res_count = Reservation.objects.filter (repeat_series=booked[0].repeat_series) \
                                       .aggregate (Count ('id'))['id__count']
        self.assertEquals (res_count, len(booked))
        #
        # data correctness for all saved reservations
        #
        for idx in range (0, len(booked)):
            new_booking = Reservation.objects.get (pk=booked[idx].id)
            for_date = from_date + timedelta (days=idx*7)
            
            self.assertEquals (new_booking.for_date, for_date)
            self.assertEquals (new_booking.vacancy, v)
            self.assertEquals (new_booking.user, self.club.user)
            self.assertEquals (new_booking.type, 'C')
            self.assertEquals (new_booking.description, desc)
            self.assertEquals (new_booking.repeat_series, booked[0].repeat_series)
            
    
    def test_manager_get_next_repeat_series (self):
        """
        The retrieved identifier should be valid (i.e. not existing in DB).-
        """
        next_id = Reservation.objects.get_next_repeat_series ( )
        res_count = Reservation.objects.filter (repeat_series=next_id) \
                                       .aggregate (Count ('id'))
        self.assertEquals (res_count['id__count'], 0)
    
    
    def test_manager_book (self):
        """
        Checks correct booking of free vacancy terms.-
        """
        #
        # cannot book a taken term
        #
        r = random.choice (self.res_list)
        taken_term = r.vacancy
        for_date = r.for_date
        description = "Testing the book (...) method"
        repeat_series = None
        booking = Reservation.objects.book (for_date=for_date, 
                                            vacancy=taken_term, 
                                            user=self.player.user, 
                                            description=description,
                                            repeat_series=repeat_series)
        self.assertIsNone (booking)
        #
        # the court should be available
        #
        cs = CourtSetup.objects.get_active (self.club)
        court_off = Court.objects.filter (court_setup=cs) \
                                 .filter (is_available=False)
        if court_off:
            court_off = court_off[0]
            for_date = date.today ( ) + timedelta(days=random.randint (0, 5))
            hour = Vacancy.HOURS[random.randint(0, 15)][0]
            term = Vacancy.objects.get (court=court_off,
                                        day_of_week=for_date.isoweekday ( ),
                                        available_from=hour)
            description = "Testing the book (...) method"
            repeat_series = None
            booking = Reservation.objects.book (for_date=for_date, 
                                                vacancy=term, 
                                                user=self.player.user, 
                                                description=description,
                                                repeat_series=repeat_series)
            self.assertIsNone (booking)
        #
        # reservations should be correctly created
        # and commit works as expected
        #
        cs = CourtSetup.objects.get_active (self.club)
        for court in Court.objects.get_available (cs).iterator ( ):
            for_date = date.today ( ) + timedelta(days=random.randint (0, 5))
            hour = Vacancy.HOURS[random.randint(0, 15)][0]
            term = Vacancy.objects.get (court=court,
                                        day_of_week=for_date.isoweekday ( ),
                                        available_from=hour)
            description = "Testing the book (...) method"
            repeat_series = court.number * 10
            commit = not (court.number%2 == 0)
            
            free_terms = [t['id'] for t in Vacancy.objects.get_free (cs, for_date, hour).values ('id')]
            booking = Reservation.objects.book (for_date=for_date, 
                                                vacancy=term, 
                                                user=self.player.user if court.number%2 == 0 else self.club.user, 
                                                description=description,
                                                repeat_series=repeat_series,
                                                commit=commit)
            if term.id in free_terms:
                #
                # the term was free, reservation should be ok; it
                # should also appear in the DB if commit was True
                #
                try:
                    new_booking = Reservation.objects.get (pk=booking.id)
                    #
                    # reservation appears in the DB: commit should be True
                    #
                    self.assertTrue (commit)
                except ObjectDoesNotExist:
                    #
                    # reservation has not been saved: commit should be False
                    #
                    new_booking = booking
                    self.assertFalse (commit)
                self.assertEquals (new_booking.for_date, for_date)
                self.assertEquals (new_booking.vacancy, term)
                if court.number%2 == 0:
                    self.assertEquals (new_booking.user, self.player.user)
                    self.assertEquals (new_booking.type, 'P')
                else:
                    self.assertEquals (new_booking.user, self.club.user)
                    self.assertEquals (new_booking.type, 'C')
                self.assertEquals (new_booking.description, description)
                self.assertEquals (new_booking.repeat_series, repeat_series)
            else:
                #
                # the term was taken, booking should fail
                #
                self.assertIsNone (booking)
            
        
    def test_manager_copy_individual_reservations_to_court_setup (self):
        """
        Correctly copy reservations to another court setup.-
        """
        source_cs = self.res_list[0].vacancy.court.court_setup
        #
        # get a court setup capable of accommodating all
        # reservations of the source court setup
        #
        for cs in self.cs_list:
            target_cs = CourtSetup.objects.get (pk=cs.id)
            if source_cs != target_cs:
                for r in Reservation.objects.by_court_setup (cs):
                    free_terms = Vacancy.objects.get_free (cs, 
                                                           r.for_date, 
                                                           r.vacancy.available_from)
                    free_terms = free_terms.aggregate (Count ('id'))
                    if free_terms['id__count'] == 0:
                        target_cs = None
                #
                # did we find a target court setup?
                #
                if target_cs is not None:
                    break
        #
        # make sure the target court setup is valid
        #            
        self.assertIsNotNone (target_cs)
        self.assertIsInstance (target_cs, CourtSetup)
        self.assertNotEquals (source_cs, target_cs)
        #
        # check that all reservations are correctly copied, without committing to DB
        # 
        source_cs_count = Reservation.objects.by_court_setup (source_cs) \
                                             .aggregate (Count ('id'))['id__count']
        target_cs_count = Reservation.objects.by_court_setup (target_cs) \
                                             .aggregate (Count ('id'))['id__count']
        copied = Reservation.objects.copy_to_court_setup (target_cs, self.res_list, commit=False)
        self.assertEquals (len (copied), len (self.res_list)) 
        self.assertEquals (Reservation.objects.by_court_setup (source_cs).aggregate (Count('id'))['id__count'],
                           source_cs_count)
        self.assertEquals (Reservation.objects.by_court_setup (target_cs).aggregate (Count('id'))['id__count'],
                           target_cs_count)
        #
        # check that all reservations are correctly copied, but saving to DB
        # 
        source_cs_count = Reservation.objects.by_court_setup (source_cs) \
                                             .aggregate (Count ('id'))['id__count']
        target_cs_count = Reservation.objects.by_court_setup (target_cs) \
                                             .aggregate (Count ('id'))['id__count']
        copied = Reservation.objects.copy_to_court_setup (target_cs, self.res_list, commit=True)
        self.assertEquals (len (copied), len (self.res_list))
        self.assertEquals (Reservation.objects.by_court_setup (source_cs).aggregate (Count('id'))['id__count'],
                           source_cs_count)
        self.assertEquals (Reservation.objects.by_court_setup (target_cs).aggregate (Count('id'))['id__count'],
                           len(self.res_list) + target_cs_count)
        #
        # check that all copied reservations are correct
        #
        for src_r in self.res_list:
            tgt_r = Reservation.objects.by_date (target_cs, src_r.for_date) \
                                       .filter (created_on=src_r.created_on) \
                                       .filter (vacancy__court__number=src_r.vacancy.court.number) \
                                       .filter (vacancy__available_from=src_r.vacancy.available_from)
            if len(tgt_r) == 0:
                tgt_r = Reservation.objects.by_date (target_cs, src_r.for_date) \
                                           .filter (created_on=src_r.created_on) \
                                           .filter (vacancy__available_from=src_r.vacancy.available_from)
            tgt_r = tgt_r[0]
            self.assertIsNotNone (tgt_r)
            self.assertIsInstance (tgt_r, Reservation)
            self.assertEquals (src_r.created_on, tgt_r.created_on)
            self.assertEquals (src_r.for_date, tgt_r.for_date)
            self.assertEquals (src_r.vacancy.day_of_week, tgt_r.vacancy.day_of_week)
            self.assertEquals (src_r.vacancy.available_from, tgt_r.vacancy.available_from)
            self.assertEquals (src_r.vacancy.available_to, tgt_r.vacancy.available_to)
            self.assertEquals (target_cs, tgt_r.vacancy.court.court_setup)
            self.assertEquals (src_r.user, tgt_r.user)
            self.assertEquals (src_r.description, tgt_r.description)
            self.assertEquals (src_r.repeat_series, tgt_r.repeat_series)

        
    def test_manager_copy_repeating_reservations_to_court_setup (self):
        """
        Correctly copy reservations to another court setup.-
        """
        #
        # add a repeating reservation, making sure we can accommodate it
        #
        source_cs = CourtSetup.objects.get_active (self.club)
        from_date = date.today ( ) + timedelta (days=random.randint (0, 10))
        until_date = from_date + timedelta (days=random.randint (8, 25))
        vacancy = None
        while vacancy is None:
            vacancy = Vacancy.objects.get_free (source_cs, 
                                                from_date, 
                                                Vacancy.HOURS[random.randint(0, 15)][0])
            vacancy = vacancy[0] if vacancy else None
            
        booked = Reservation.objects.book_weekly (from_date, until_date, commit=False,
                                                  vacancy=vacancy,
                                                  description="Testing description",
                                                  user=self.club.user)
        self.assertEquals (len(booked), 
                           Reservation.objects.get_weekly_reservation_count (from_date,
                                                                             until_date))
        booked = Reservation.objects.book_weekly (from_date, until_date, commit=True,
                                                  vacancy=vacancy,
                                                  description="Testing description",
                                                  user=self.club.user)
        self.assertEquals (len(booked), 
                           Reservation.objects.get_weekly_reservation_count (from_date,
                                                                             until_date))
        #
        # try to copy the repeating reservations to another court setup
        #
        target_cs = source_cs
        while target_cs == source_cs:
            target_cs = random.choice (self.cs_list)
        
        booked_copy = Reservation.objects.copy_to_court_setup (target_cs, booked, commit=False)
        self.assertTrue (len (booked_copy) <= len (booked))
        #
        # check the correctness of the copied and (possibly)
        # not copied reservations
        #
        repeat_id = booked_copy[0].repeat_series
        for tgt_r in booked_copy:
            for src_r in booked:
                if src_r.for_date == tgt_r.for_date:
                    self.assertEquals (src_r.for_date, tgt_r.for_date)
                    self.assertEquals (src_r.vacancy.day_of_week, tgt_r.vacancy.day_of_week)
                    self.assertEquals (src_r.vacancy.available_from, tgt_r.vacancy.available_from)
                    self.assertEquals (src_r.vacancy.available_to, tgt_r.vacancy.available_to)
                    self.assertEquals (target_cs, tgt_r.vacancy.court.court_setup)
                    self.assertEquals (src_r.user, tgt_r.user)
                    self.assertEquals (src_r.description, tgt_r.description)
                    self.assertEquals (tgt_r.repeat_series, repeat_id)
                    booked.pop (booked.index (src_r))
        #
        # check that not copied reservations have their target
        # terms actually taken
        #
        for src_r in booked:
            tgt_v = Vacancy.objects.get_free (target_cs,
                                              src_r.for_date,
                                              src_r.vacancy.available_from)
            tgt_v = tgt_v.aggregate (Count ('id'))
            self.assertTrue (tgt_v['id__count'], 0)
   
    
    def test_default_type_is_player (self):
        """
        The default reservation type should be 'by player'.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        c = Court.objects.get_available (cs)
        for i in range (0, random.randint (1, 7)):
            v = Vacancy.objects.get_all ([c[0]], [Vacancy.DAYS[i][0]])
            try:
                r = Reservation.objects.create (for_date=date.today ( ),
                                                description="Test reservation",
                                                user=self.player.user,
                                                vacancy=v[i])
                r.save ( )
                r = Reservation.objects.get (pk=r.id)
                self.assertEquals (r.type, 'P')
            except IntegrityError:
                pass
            
                
    def test_cannot_delete_reserved_vacancy (self):
        """
        A reservation cannot be deleted indirectly by deleting the 
        referenced vacancy.-
        """
        #
        # try to indirectly delete some reservations via their
        # referenced vacancies (should throw exception)
        #
        v_ids = Reservation.objects.filter (user=self.player.user) \
                                   .values ('vacancy__id')
        for v in v_ids:
            try:
                Vacancy.objects.get (pk=v['vacancy__id']).delete ( )
                self.assertTrue (False)
            except ProtectedError:
                self.assertTrue (True)
                
                
    def test_manager_by_date (self):
        """
        Checks that the number of reservations returned
        by this method is correct.-
        """
        cs = random.choice (self.cs_list)
        court_count = Court.objects.get_count (cs)
        hour_count = len (Vacancy.HOURS) - 1
        term_count = court_count * hour_count
        for_date = date.today ( )
        booked = Reservation.objects.by_date (cs, for_date) \
                                    .values ('vacancy__id')
        free = Vacancy.objects.filter (court__court_setup=cs) \
                              .filter (day_of_week=for_date.isoweekday ( )) \
                              .exclude (id__in=booked) \
                              .values ('id')
        self.assertEquals (term_count, len(booked) + len(free))
        
            
    def test_manager_from_date (self):
        """
        Checks that the number of reservations returned
        by this method is correct.-
        """
        cs = random.choice (self.cs_list)
        court_count = Court.objects.get_count (cs)
        from_date = date.today ( )
        booked_dates = Reservation.objects.from_date (cs, from_date) \
                                          .values ('for_date').distinct ( )
        hour_count = len (Vacancy.HOURS) - 1
        term_count = court_count * len(booked_dates) * hour_count
        booked = Reservation.objects.from_date (cs, from_date) \
                                    .values ('vacancy__id')
        free_count = 0
        for d in booked_dates:
            free = Vacancy.objects.filter (court__court_setup=cs) \
                                  .filter (day_of_week=d['for_date'].isoweekday ( )) \
                                  .exclude (id__in=booked) \
                                  .values ('id')
            free_count += len (free)
        self.assertEquals (term_count, len(booked) + free_count)
        
