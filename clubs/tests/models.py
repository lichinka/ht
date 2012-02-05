import random
from datetime import date, timedelta

from django.db.models import Count
from django.utils.translation import ugettext

from clubs.models import CourtSetup, Court, Vacancy
from reservations.models import Reservation
from ht_utils.tests.views import BaseViewTestCase

        
    
class CourtSetupTest (BaseViewTestCase):
    """
    All the test cases for the CourtSetup model.-
    """
    def setUp (self):
        pass
   
    
    def test_default_court_setup_creation (self):
        """
        Checks that a default court setup has been created for the new club.-
        """
        #
        # create a club
        #
        BaseViewTestCase._create_club (self)
        
        self.assertIsNotNone (CourtSetup.objects.get_active (self.club))
        cs = CourtSetup.objects.get_active (self.club)
        self.assertEquals (cs.name, ugettext ('Default'))
        self.assertEquals (cs.club, self.club)
        self.assertTrue (cs.is_active)


    def test_manager_activate (self):
        """
        Checks that court setup activation is correctly handled.-
        """
        #
        # create some court setups
        #
        BaseViewTestCase._add_court_setups (self)

        #
        # active court setups
        #       
        active = CourtSetup.objects.filter (club=self.club) \
                                   .filter (is_active=True)
        #
        # activate random court setups
        #
        for i in range (0, random.randint (2, 5)):
            rand_cs = random.choice (self.cs_list)
            CourtSetup.objects.activate (rand_cs)
            self.assertEquals (active.aggregate (Count ('id'))['id__count'], 1)
            for cs in CourtSetup.objects.filter (club=self.club).iterator ( ):
                self.assertEquals (cs.is_active, cs==rand_cs)


    def test_manager_delete_1 (self):
        """
        A court setup with reservations cannot be deleted if the
        'force' flag is set to False (default).-
        """
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # activate a random court setup, so that we will check
        # that it remains active after calling delete
        #
        CourtSetup.objects.activate (random.choice (self.cs_list))
        act_cs = CourtSetup.objects.get_active (self.club)
        #
        # find a court setup with reservations attached to it
        #
        for i in range (0, random.randint (1, len (self.res_list))):
            rand_res = random.choice (self.res_list)
            cs = rand_res.vacancy.court.court_setup
            #
            # avoid working with the active court setup,
            # since this should be tested elsewhere
            #
            if cs == act_cs:
                continue
            else:
                #
                # a court setup, that has reservations
                # attached to it, must not be deleted
                #
                cs_count = CourtSetup.objects.get_count (self.club)
                self.assertGreater (cs_count, 1)
                CourtSetup.objects.delete (cs)
                self.assertEquals (cs_count, CourtSetup.objects.get_count (self.club))
                self.assertEquals (act_cs, CourtSetup.objects.get_active (self.club))
    
    
    def test_manager_delete_2 (self):
        """
        There always should be an active court setup,
        even if the active one has been deleted.-
        """
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # if the active court setup has been deleted,
        # another one should still be active
        #
        cs = CourtSetup.objects.get_active (self.club)
        self.assertIsNotNone (cs)
        CourtSetup.objects.delete (cs, force=True)
        cs_act = CourtSetup.objects.get_active (self.club)
        self.assertIsNotNone (cs_act)
        self.assertNotEquals (cs_act, cs)
        self.assertEquals (cs_act.is_active, True)

        
    def test_manager_delete_3 (self):
        """
        Checks that the 'force' flag works correctly.-
        """
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # successfully delete a court setup that has reservations 
        # attached to it, if and only if the 'force' flag is True
        #
        cs_count = CourtSetup.objects.get_count (self.club)
        self.assertGreater (cs_count, 1)
        #
        # find a court setup with reservations attached to it
        #
        rand_res = random.choice (self.res_list)
        cs = rand_res.vacancy.court.court_setup
        #
        # force the deletion of the court setup
        #
        CourtSetup.objects.delete (cs, force=True)
        self.assertEquals (cs_count, CourtSetup.objects.get_count (self.club) + 1)

        
    def test_manager_delete_4 (self):
        """
        Checks successful deletion of a random court setup.-
        """
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # successful deletion of a random court setup ...
        #
        cs = random.choice (self.cs_list)
        self.assertEquals (cs.club, self.club)
        cs_count = CourtSetup.objects.get_count (self.club)
        CourtSetup.objects.delete (cs, force=True)
        #
        # ... or not deletion, if it is the last one 
        # 
        if cs_count > 1:
            self.assertEquals (cs_count, CourtSetup.objects.get_count (self.club) + 1)
            cs_act = CourtSetup.objects.get_active (self.club)
            self.assertIsNotNone (cs_act)
            self.assertNotEquals (cs_act, cs)
            self.assertEquals (cs_act.is_active, True)
        else:
            self.assertEquals (CourtSetup.objects.get_count (self.club), 1)

        
    def test_manager_delete_5 (self):
        """
        The last court setup cannot be deleted and should always be active.-
        """
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # the last court setup cannot be deleted and should always be active
        #
        for cs in self.cs_list:
            CourtSetup.objects.delete (cs, force=True)
            cs_count = CourtSetup.objects.get_count (self.club)
            self.assertTrue (cs_count > 0)
            self.assertIsInstance (CourtSetup.objects.get_active (self.club), CourtSetup)
            
        for i in range (0, 10):
            cs = CourtSetup.objects.get_active (self.club)
            CourtSetup.objects.delete (cs, force=True)
            cs_count = CourtSetup.objects.get_count (self.club)
            self.assertEquals (cs_count, 1)
            self.assertEquals (cs.is_active, True)
            
            
    def test_manager_clone (self):
        """
        Checks that a court setup is correctly cloned.-
        """
        #
        # add some courts
        #
        BaseViewTestCase._add_courts (self)
        
        cs_clone = CourtSetup.objects.clone (self.cs_list[1])
        self.assertEquals (cs_clone.name, "%s %s" % (ugettext('Copy of'), self.cs_list[1].name))
        self.assertEquals (cs_clone.club, self.club)
        self.assertEquals (cs_clone.is_active, False)
      
        for c in Court.objects.get_available (self.cs_list[1]):
            c_clone = Court.objects.get_available (cs_clone).filter (number=c.number)
            self.assertEquals (c_clone.aggregate (Count ('id'))['id__count'], 1,
                               "Court %s does not exist in cloned court setup" % str(c.number))
            c_clone = c_clone[0]
            self.assertIsInstance (c_clone, Court)
            self.assertEquals (c_clone.court_setup, cs_clone)
            self.assertEquals (c_clone.number, c.number)
            self.assertEquals (c_clone.indoor, c.indoor)
            self.assertEquals (c_clone.light, c.light)
            self.assertEquals (c_clone.surface, c.surface)
            self.assertEquals (c_clone.single_only, c.single_only)
            self.assertEquals (c_clone.is_available, c.is_available)
            
        cs_clone = CourtSetup.objects.clone (CourtSetup.objects.get_active (self.club)) 
        self.assertEquals (cs_clone.name, 
                           "%s %s" % (ugettext('Copy of'), CourtSetup.objects.get_active (self.club).name))
        self.assertEquals (cs_clone.club, self.club)
        self.assertEquals (cs_clone.is_active, False)
        
        for c in Court.objects.get_available (CourtSetup.objects.get_active (self.club)):
            c_clone = Court.objects.get_available (cs_clone).filter (number=c.number)
            self.assertEquals (c_clone.aggregate (Count ('id'))['id__count'], 1,
                               "Court %s does not exist in cloned court setup" % str(c.number))
            c_clone = c_clone[0]
            self.assertIsInstance (c_clone, Court)
            self.assertEquals (c_clone.court_setup, cs_clone)
            self.assertEquals (c_clone.number, c.number)
            self.assertEquals (c_clone.indoor, c.indoor)
            self.assertEquals (c_clone.light, c.light)
            self.assertEquals (c_clone.surface, c.surface)
            self.assertEquals (c_clone.single_only, c.single_only)
            self.assertEquals (c_clone.is_available, c.is_available)


    
class CourtTest (BaseViewTestCase):
    """
    All the test cases for the Court model.-
    """
    def setUp (self):
        #
        # different tests need different states
        #
        pass

    def test_default_court_creation (self):
        """
        Checks that a default court has been created for the new club
        inside its default court setup.-
        """
        #
        # create a club
        #
        BaseViewTestCase._create_club (self)
        
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        court_count = courts.aggregate (Count ('id'))
        court_count = int(court_count['id__count'])
        
        self.assertEquals (court_count, 1)
        self.assertEquals (courts[0].number, 1)
        self.assertEquals (courts[0].court_setup, cs)
        

    def test_manager_delete_reservations (self):
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # pick a random reservation
        #
        res = random.choice (self.res_list)
        court = res.vacancy.court
        #
        # count reservations at court setup level
        #
        cs_res_count = Reservation.objects.by_court_setup (court.court_setup) \
                                          .aggregate (Count ('id'))
        cs_res_count = cs_res_count['id__count']
        self.assertGreater (cs_res_count, 0)
        #
        # count reservations at court level
        #
        res_count = Reservation.objects.by_court_setup (court.court_setup) \
                                       .filter (vacancy__court=court) \
                                       .aggregate (Count ('id'))
        res_count = res_count['id__count']
        self.assertGreater (res_count, 0)
        #
        # delete all reservations attached to this court
        #
        Court.objects.delete_reservations (court)
        self.assertEquals (cs_res_count - res_count,
                           Reservation.objects.by_court_setup (court.court_setup) \
                                      .aggregate (Count ('id'))['id__count'])
        #
        # add a repeating reservation
        #
        cs = CourtSetup.objects.get_active (self.club)
        hour = random.choice (Vacancy.HOURS[:-1])
        from_date = date.today ( )
        until_date = from_date + timedelta (days=random.randint (10, 35))
        v = None
        while v is None:
            v = Vacancy.objects.get_free (cs, from_date, hour[0]).values ('id')
            v = random.choice (v) if v else None
        v = Vacancy.objects.get (pk=v['id'])
        booked = Reservation.objects.book_weekly (from_date,
                                                  until_date,
                                                  vacancy=v,
                                                  user=self.club.user,
                                                  commit=True)
        #
        # count reservations at court setup level
        #
        cs_res_count = Reservation.objects.by_court_setup (cs) \
                                          .aggregate (Count ('id'))
        cs_res_count = cs_res_count['id__count']
        self.assertGreater (cs_res_count, 0)
        #
        # count reservations at court level
        #
        court = booked[0].vacancy.court
        res_count = Reservation.objects.by_court_setup (court.court_setup) \
                                       .filter (vacancy__court=court) \
                                       .aggregate (Count ('id'))
        res_count = res_count['id__count']
        self.assertGreaterEqual (res_count, len (booked))
        #
        # now delete the repeating reservations, by deleting their court
        #
        Court.objects.delete_reservations (court)
        self.assertEquals (cs_res_count - res_count,
                           Reservation.objects.by_court_setup (court.court_setup) \
                                              .aggregate (Count ('id'))['id__count'])


class VacancyTest (BaseViewTestCase):
    """
    All the test cases for the Vacancy model.-
    """
    def setUp (self):
        #
        # different tests need different states
        #
        pass
    
    def test_default_vacancy_terms_creation (self):
        """
        Checks that default vacancy terms are created for the new club
        inside its default court setup, as part of its default court.-
        """
        #
        # add some courts
        #
        BaseViewTestCase._add_courts (self)
        
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        vacancy_terms = Vacancy.objects.get_all (courts)
        
        all_days = [k for k,v in Vacancy.DAYS]
        all_hours = [k for k,v in Vacancy.HOURS]
        
        for c in courts.iterator ( ):
            for d in all_days:
                for i in range (0, len(all_hours[:-1])):
                    h = all_hours[i]
                    v = Vacancy.objects.get_all ([c], [d], [h])
                    vacancy_count = v.aggregate (Count ('id'))
                    vacancy_count = int (vacancy_count['id__count'])
                    
                    self.assertTrue (vacancy_count == 1,
                                     "Vacancy count returned more than one element")
                    v = v[0]
                    
                    self.assertTrue (v.court == c,
                                     "The vacancy term %s does not belong to court %s" % (v, c))
                    self.assertTrue (v.day_of_week == d,
                                     "The vacancy term %s has an invalid day" % v)
                    self.assertTrue (v.available_from == h,
                                     "The vacancy term %s has an invalid starting time" % v)
                    self.assertTrue (v.available_to == all_hours[i+1],
                                     "The vacancy term %s has an invalid ending time" % v)
                    self.assertIsNotNone (v.price == None)
                    self.assertTrue (v in vacancy_terms,
                                     "The vacancy term %s is not contained in the 'get_all' query" % v)
                    
                last_vacancy = Vacancy.objects.get_all ([c], [d], [all_hours[-1]])
                last_vacancy = last_vacancy.aggregate (Count ('id'))
                last_vacancy = int (last_vacancy['id__count'])
                
                self.assertTrue (last_vacancy == 0,
                                 "The vacancy terms for court %s contain the last time interval %s" % (c,
                                                                                                       all_hours[-1]))
    
    def test_days (self):
        """
        Checks that all days are part of the vacancy terms.-
        """
        self.assertTrue (len (Vacancy.DAYS) == 7,
                         "Vacancy.DAYS does not contain all expected days.")
        
    def test_hours (self):
        """
        Checks that all expected hours are part of the vacancy terms.-
        """
        self.assertTrue (len (Vacancy.HOURS) == 18,
                         "Vacancy.HOURS does not contain all expected hours.")
        self.assertTrue (Vacancy.HOURS[0] == (7, '7:00'),
                         "Vacancy.HOURS first element is not as expected.")
        self.assertTrue (Vacancy.HOURS[-1] == (24, '24:00'),
                         "Vacancy.HOURS last element is not as expected.")
    
    def test_manager_get_free (self):
        """
        Checks the correctness of the get_free manager method.- 
        """
        #
        # add some reservations
        #
        BaseViewTestCase._add_reservations (self)
        #
        # test everything with available courts only
        #
        for_date = date.today ( )
        hour = random.choice (Vacancy.HOURS[:-1])
        cs = random.choice (self.cs_list)
        term_count = Court.objects.get_available (cs) \
                                  .aggregate (Count ('id'))
        term_count = term_count['id__count']
        booked = Reservation.objects.by_date (cs, for_date) \
                                    .filter (vacancy__court__is_available=True) \
                                    .filter (vacancy__available_from=hour[0]) \
                                    .values ('vacancy__id')
        free = Vacancy.objects.get_free (cs, for_date, hour[0]) \
                              .values ('id')
        self.assertEquals (term_count, len(booked) + len(free))
        #
        # randomly deactivate a court and repeat the test
        #
        court_off = random.choice (Court.objects.get_available (cs).values ('id'))
        court_off = Court.objects.get (pk=court_off['id'])
        court_off.is_available = False
        court_off.save ( )
        for_date = date.today ( )
        hour = random.choice (Vacancy.HOURS[:-1])
        cs = random.choice (self.cs_list)
        term_count = Court.objects.get_available (cs)
        term_count = term_count.aggregate (Count ('id'))['id__count']
        booked = Reservation.objects.by_date (cs, for_date) \
                                    .filter (vacancy__available_from=hour[0]) \
                                    .values ('vacancy__id')
        free = Vacancy.objects.get_free (cs, for_date, hour[0]) \
                              .values ('id')
        self.assertEquals (term_count, len(booked) + len(free))
    
        
    def test_manager_get_all (self):
        """
        Checks the correctness of the get_all manager method.- 
        """
        #
        # add some vacancies
        #
        BaseViewTestCase._add_vacancy_prices (self)
        
        cs = random.choice (self.cs_list)
        courts = Court.objects.get_available (cs)
        vacancy_terms = Vacancy.objects.get_all (courts)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should be 119 terms per court, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 
                           119 * int (courts.aggregate (Count ('id'))['id__count']))
        #
        # the method should also accept a list of objects
        #
        courts = Court.objects.get_available (cs).iterator ( )
        court_list = [c for c in courts]
        vacancy_terms = Vacancy.objects.get_all (court_list)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should still be 119 terms per court, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 
                           119 * int (Court.objects.get_available (cs).aggregate (Count ('id'))['id__count']))
        #
        # the method should also accept a list of IDs
        #
        courts = Court.objects.get_available (cs).iterator ( )
        court_list = [c.id for c in courts]
        vacancy_terms = Vacancy.objects.get_all (court_list)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should still be 119 terms per court, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 
                           119 * int (Court.objects.get_available (cs).aggregate (Count ('id'))['id__count']))
        #
        # the method should also accept a list of dicts
        #
        court_list = Court.objects.get_available (cs).values ( )
        vacancy_terms = Vacancy.objects.get_all (court_list)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should still be 119 terms per court, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 
                           119 * int (Court.objects.get_available (cs).aggregate (Count ('id'))['id__count']))
        