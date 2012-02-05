from random import randint
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from ht_utils import number_to_default_locale
from clubs.models import CourtSetup, Court, Vacancy
from clubs.templatetags import vacancy_tags
from reservations.models import Reservation
from ht_utils.tests.views import BaseViewTestCase



class VacancyPerHourTagTest (BaseViewTestCase):
    """
    All the test cases for the template tags of this app.-
    """
    def setUp (self):
        BaseViewTestCase._add_courts (self)
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
                
    def test (self):
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
                        
                        
                        
class VacancyPricesPerDayTagTest (BaseViewTestCase):
    def setUp (self):
        BaseViewTestCase._add_vacancy_prices (self)
        
    def test (self):
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
                