from random import randint
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from django.test import TestCase
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext
from django.contrib.auth.models import User

from ht_utils import number_to_default_locale, random_id_list
from ht_utils import pick_random_element, BaseViewTestCase
from clubs.models import CourtSetup, Court, Vacancy
from accounts.models import UserProfile
from locations.models import City
from clubs.templatetags import vacancy_tags
from reservations.models import Reservation
from clubs.templatetags.vacancy_tags import vacancy_prices_per_day



class TemplateTagTest (TestCase):
    """
    All the test cases for the template tags of this app.-
    """
    def setUp (self):
        """
        Creates a club and fills prices for some vacancy terms
        used during testing.-
        """
        c = User.objects.create_user ('test_club', 'club@nowhere.si', 'pass')
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")
        #
        # set some prices for the vacancy terms of all
        # courts in the active court setup
        #
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        for c in courts:
            court_vacancy_terms = Vacancy.objects.get_all ([c])
            for v in court_vacancy_terms:
                v.price = Decimal ('%10.2f' % float(1.03 * c.id + 1.07 * v.available_from))
                v.save ( )
                
                
    def test_vacancy_per_hour (self):
        """
        Checks the behavior of tag vacancy_per_hour.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        for_date = date.today ( )
       
        #
        # without reservations, all vacancy prices should match
        # 
        for c in courts:
            vacancy_list = vacancy_tags.vacancy_per_hour (c, for_date, Vacancy.HOURS[:-1])
            self.assertEquals (len (vacancy_list['hour_list']), len (Vacancy.HOURS[:-1]))
            for v in vacancy_list['hour_list']:
                expected = '%10.2f' % float (1.03 * c.id + 1.07 * v['value'])
                expected = Decimal (expected).quantize (Decimal ('.01'), 
                                                        rounding=ROUND_HALF_UP)
                self.assertEquals (v['vacancy'].price, expected)
                
        #
        # check that randomly reserved vacancy terms do not appear as free,
        # others should still be available
        #
        rand_vacancy_list = []
        for c in courts:
            vacancy_list = vacancy_tags.vacancy_per_hour (c, for_date, Vacancy.HOURS[:-1])
            vacancy_list = vacancy_list['hour_list']
            for i in range (0, 3):
                exist = True
                while exist:
                    rand_vacancy = randint (1, len (vacancy_list))
                    rand_vacancy = vacancy_list[rand_vacancy - 1]['vacancy']
                    exist = Reservation.objects.filter (for_date=date.today ( ),
                                                        vacancy=rand_vacancy)
                Reservation.objects.create (for_date=date.today ( ),
                                            description="Test reservation",
                                            user=self.club.user,
                                            vacancy=rand_vacancy)
                rand_vacancy_list.append (rand_vacancy)
        
        for reserved_vacancy in rand_vacancy_list:
            for c in courts:
                vacancy_list = vacancy_tags.vacancy_per_hour (c, for_date, Vacancy.HOURS[:-1])
                self.assertEquals (len (vacancy_list['hour_list']), len (Vacancy.HOURS[:-1]))
                for v in vacancy_list['hour_list']:
                    if v['vacancy'] == reserved_vacancy:
                        self.assertIsNotNone (v['reservation'])
                    else:
                        if v['reservation']:
                            self.assertTrue (v['reservation'].vacancy in rand_vacancy_list)
                        
                        
                        
    def test_vacancy_prices_per_day (self):
        """
        Checks the behavior of tag vacancy_prices_per_day.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        hours = [k for (k,v) in Vacancy.HOURS[:-1]]
        
        for c in courts:
            for h in hours:
                prices = vacancy_tags.vacancy_prices_per_day (c, h)
                prices = prices.values ( )[0]
                days = [k for k,v in Vacancy.DAYS]
                
                self.assertTrue (len(days) == len(prices),
                                 "Tag vacancy_prices_per_day returned a wrong number of prices")
               
                for i in range (0, len(days)):
                    (p_id, p_value) = prices[i]
                    vacancy_id = int (p_id.split ('_')[-1])
                    try:
                        vacancy_price = Decimal ('%10.2f' % float (number_to_default_locale (p_value)))
                    except ValueError:
                        vacancy_price = None
                    v = Vacancy.objects.get (pk=vacancy_id)
                    
                    self.assertTrue (v.day_of_week == days[i],
                                     "Vacancy %s has incorrect day" % vacancy_id)
                    if v.price:
                        self.assertEquals (v.price, vacancy_price,
                                           "Vacancy %s price does not match" % vacancy_id)
                    else:
                        self.assertIsNone (vacancy_price,
                                           "Vacancy %s should be None" % vacancy_id)
                
            
                
class DeleteCourtSetupTest (BaseViewTestCase):
    """
    All the test cases for this view.-
    """
    def test_having_an_active_court_setup_after_deleting_the_active_one (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        #
        # if the active court setup has been deleted, another one 
        # should still be active
        #
        cs = CourtSetup.objects.get_active (self.club)
        self.assertIsNotNone (cs)
        view_url = reverse ('clubs.views.delete_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        cs_act = CourtSetup.objects.get_active (self.club)
        self.assertIsNotNone (cs_act)
        self.assertNotEquals (cs_act, cs)
        self.assertEquals (cs_act.is_active, True)
        
    
    def test_cannot_delete_court_setup_with_reservations (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        #
        # cannot delete a court setup that has reservations attached to it
        #
        cs_count = CourtSetup.objects.get_count (self.club)
        # create reservation
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs).values ( )
        v = False
        while not v:
            v = Vacancy.objects.get_all_by_date (courts,
                                                 [date.today ( )],
                                                 [pick_random_element (Vacancy.HOURS)[0]])
        Reservation.objects.create (for_date=date.today ( ),
                                    type='P',
                                    description="Test reservation",
                                    user=self.player.user,
                                    vacancy=v[0])
        # try to delete the court setup
        cs = CourtSetup.objects.get (pk=cs.id)
        view_url = reverse ('clubs.views.delete_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (cs_count, CourtSetup.objects.get_count (self.club))
   
    
    def test_successful_deletion_of_a_random_court_setup (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        #
        # successful deletion of a random court setup
        #
        cs_ids = random_id_list (CourtSetup.objects.all ( ).values ('id'))
        cs_count = CourtSetup.objects.get_count (self.club)
        cs = CourtSetup.objects.get (pk=cs_ids[0])
        view_url = reverse ('clubs.views.delete_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (cs_count, CourtSetup.objects.get_count (self.club) + 1)
        # successful redirection after successful deletion
        self.assertEquals (resp.template[0].name, 'accounts/display_club_profile.html')
    
    
    def test_the_last_court_setup_cannot_be_deleted_and_should_be_active (self):
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'], 
                        password=self.T_CLUB['password'])
        #
        # the last court setup cannot be deleted and should always be active
        #
        cs_ids = random_id_list (CourtSetup.objects.filter (club=self.club).values ('id'))
        for id in cs_ids:
            view_url = reverse ('clubs.views.delete_court_setup',
                                args=[id])
            resp = self.cli.get (view_url, follow=True)
            self.assertEquals (resp.status_code, 200)
            cs_count = CourtSetup.objects.get_count (self.club)
            self.assertTrue (cs_count > 0)
            self.assertIsInstance (CourtSetup.objects.get_active (self.club), CourtSetup)
        for i in range (0, 10):
            cs = CourtSetup.objects.get_active (self.club)
            view_url = reverse ('clubs.views.delete_court_setup',
                                args=[cs.id])
            resp = self.cli.get (view_url, follow=True)
            self.assertEquals (resp.status_code, 200)
            cs_count = CourtSetup.objects.get_count (self.club)
            self.assertEquals (cs_count, 1)
            self.assertEquals (cs.is_active, True)
            
        
    
class ToggleActiveCourtSetupTest (BaseViewTestCase):
    def test (self):
        """
        Checks the behavior of clubs.views.toggle_active_court_setup.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # check that the active court setup cannot be deactivated
        #
        cs = CourtSetup.objects.get_active (self.club)
        view_url = reverse ('clubs.views.toggle_active_court_setup',
                            args=[cs.id])
        resp = self.cli.get (view_url, follow=True)
        self.assertEquals (resp.status_code, 200)
        cs = CourtSetup.objects.get (pk=cs.id)
        self.assertEquals (cs.is_active, True)
        #
        # check that there is always strictly one active court setup
        #
        cs = CourtSetup.objects.filter (club=self.club) \
                               .filter (is_active=True) \
                               .aggregate (Count ('id'))
        self.assertEquals (int (cs['id__count']), 1)
        #
        # check that some non-active court setup is correctly activated
        #
        cs = CourtSetup.objects.filter (club=self.club).filter (is_active=False)
        if cs:
            cs = cs[0]
            view_url = reverse ('clubs.views.toggle_active_court_setup',
                                args=[cs.id])
            resp = self.cli.get (view_url, follow=True)
            self.assertEquals (resp.status_code, 200)
            cs = CourtSetup.objects.get (pk=cs.id)
            self.assertEquals (cs.is_active, True)
        #
        # check that there is always strictly one active court setup
        #
        cs = CourtSetup.objects.filter (club=self.club) \
                               .filter (is_active=True) \
                               .aggregate (Count ('id'))
        self.assertEquals (int (cs['id__count']), 1)
        
            
class EditCourtSetupTest (BaseViewTestCase):
    def test (self):
        """
        Checks the behavior of clubs.views.edit_court_setup.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        #
        # check that the displayed data matches the test data
        #
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        for c in courts:
            view_url = reverse ('clubs.views.edit_court_setup',
                                args=[cs.id, c.id])
            resp = self.cli.get (view_url)
            self.assertTrue (resp.status_code == 200,
                             "The view %s returned %s" % (view_url,
                                                          resp.status_code))
            
            
class SaveCourtVacancyTest (BaseViewTestCase): 
    def test (self):
        """
        Checks the correct behavior of clubs.views.save_court_vacancy.-
        """
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])
        
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        for c in courts:
            court_prices = {}
            for h, hour in Vacancy.HOURS:
                prices = vacancy_prices_per_day (c, h)
                prices = dict (prices['prices'])
                for k in prices.keys ( ):
                    prices[k] = '%10.2f' % float (k.split ('_')[1])
                court_prices = dict (court_prices, **prices)
            
            view_url = reverse ('clubs.views.save_court_vacancy',
                                args=[c.id])        
            resp = self.cli.post (view_url, 
                                  court_prices, 
                                  follow=True)
            self.assertEquals (resp.status_code, 200)
            #
            # check that the saved prices match
            #
            v_ids = [int (Decimal (v)) for v in court_prices.values()]
            vacancy_list = Vacancy.objects.filter (id__in=v_ids)
            for v in vacancy_list:
                self.assertEquals (v.price, Decimal ('%10.2f' % float(v.id)))
    
   
    
    
class VacancyTest (TestCase):
    """
    All the test cases for the Vacancy model.-
    """
    def setUp (self):
        """
        Creates a club used during testing.-
        """
        c = User.objects.create_user ('test_club', 'club@nowhere.si', 'pass')
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")

    def test_default_vacancy_terms_creation (self):
        """
        Checks that default vacancy terms are created for the new club
        inside its default court setup, as part of its default court.-
        """
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
                    self.assertTrue (v.price == None,
                                     "The vacancy term %s has a price set" % v)
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
    
    
    def test_manager_get_all (self):
        """
        Checks the correctness of the get_all manager method.- 
        """
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        vacancy_terms = Vacancy.objects.get_all (courts)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should be 119 terms, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 119,
                           "Vacancy.objects.get_all() returned the wrong number of terms")
        #
        # the method should also accept a list of objects
        #
        courts = Court.objects.get_available (cs).iterator ( )
        court_list = [c for c in courts]
        vacancy_terms = Vacancy.objects.get_all (court_list)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should still be 119 terms, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 119,
                           "Vacancy.objects.get_all() returned the wrong number of terms")
        #
        # the method should also accept a list of IDs
        #
        courts = Court.objects.get_available (cs).iterator ( )
        court_list = [c.id for c in courts]
        vacancy_terms = Vacancy.objects.get_all (court_list)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should still be 119 terms, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 119,
                           "Vacancy.objects.get_all() returned the wrong number of terms")
        #
        # the method should also accept a list of dicts
        #
        court_list = Court.objects.get_available (cs).values ( )
        vacancy_terms = Vacancy.objects.get_all (court_list)
        vacancy_term_count = vacancy_terms.aggregate (Count ('id'))
        vacancy_term_count = int (vacancy_term_count['id__count'])
        #
        # there should still be 119 terms, i.e. 
        # 7 days * 17 time intervals, from 7:00 to 23:00
        #
        self.assertEquals (vacancy_term_count, 119,
                           "Vacancy.objects.get_all() returned the wrong number of terms")
        
        
        
class CourtTest (TestCase):
    """
    All the test cases for the Court model.-
    """
    def setUp (self):
        """
        Creates a club used during testing.-
        """
        c = User.objects.create_user ('test_club', 'club@nowhere.si', 'pass')
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")

    def test_default_court_creation (self):
        """
        Checks that a default court has been created for the new club
        inside its default court setup.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        court_count = courts.aggregate (Count ('id'))
        court_count = int(court_count['id__count'])
        
        self.assertTrue (court_count == 1,
                         "The court count within the active court setup is not 1")
        self.assertTrue (courts[0].number == 1,
                         "The court number is not 1")
        self.assertTrue (courts[0].court_setup == cs,
                         "The court does not belong to the current court setup")


    
class CourtSetupTest (TestCase):
    """
    All the test cases for the CourtSetup model.-
    """
    def setUp (self):
        """
        Creates a club used during testing.-
        """
        c = User.objects.create_user ('test_club', 'club@nowhere.si', 'pass')
        self.club = UserProfile.objects.create_club_profile (c,
                                                             "Postal address 1231",
                                                             City.objects.all ( )[0],
                                                             "111-222-333",
                                                             "The best tennis club d.o.o.")
        #
        # add a couple of extra court setups
        #
        self.cs2 = CourtSetup.objects.create (name="The second court setup",
                                              club=self.club,
                                              is_active=False)
        self.cs3 = CourtSetup.objects.create (name="The third court setup",
                                              club=self.club,
                                              is_active=False)
        #
        # add a random number of courts to each court setup
        #
        for cs in CourtSetup.objects.filter (club=self.club):
            for i in range (2, randint (2, 20)):
                Court.objects.create (court_setup=cs,
                                      number=i,
                                      indoor=True if i%2 == 0 else False,
                                      light=False if i%2 == 0 else True,
                                      surface=Court.SURFACES[i%5][0],
                                      single_only=True if i%2 == 0 else False,
                                      is_available=False if i%2 == 0 else True)
        
        
    def test_default_court_setup_creation (self):
        """
        Checks that a default court setup has been created for the new club.-
        """
        cs = CourtSetup.objects.get_active (self.club)
        
        self.assertIsNotNone (cs, 
                              "There is no active court setup for club %s" % (self.club))
        self.assertTrue (cs.name == ugettext('Default'),
                         "The name of the created court setup in not valid")
        self.assertTrue (cs.club == self.club,
                         "The created court setup is not connected with the created club")
        self.assertTrue (cs.is_active,
                         "The created court setup is not active")


    def test_manager_clone (self):
        """
        Checks that a court setup is correctly cloned.-
        """
        cs_clone = CourtSetup.objects.clone (self.cs2)
        self.assertEquals (cs_clone.name, "%s %s" % (ugettext('Copy of'), self.cs2.name))
        self.assertEquals (cs_clone.club, self.club)
        self.assertEquals (cs_clone.is_active, False)
      
        for c in Court.objects.get_available (self.cs2):
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
        