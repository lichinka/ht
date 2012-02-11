from random import randint
from datetime import date, timedelta

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext

from clubs.models import CourtSetup, Vacancy, Court
from ht_utils.tests.views import BaseViewTestCase



class ClubViewTest (BaseViewTestCase):
    """
    All test cases for this view.-
    """
    def setUp (self):
        BaseViewTestCase.setUp (self)
        #
        # data specific to this view
        #
        self.view_path = 'reservations.views.club_view'
        self.template_name = 'reservations/club_view.html'
        #
        # log the club in
        #
        self.cli.login (username=self.T_CLUB['username'],
                        password=self.T_CLUB['password'])

    def test_only_object_owner_has_access (self):
        self._test_only_club_has_access ( )

    def test_existance_and_correct_template (self):
        BaseViewTestCase._test_existance_and_correct_template (self,
                                                               self.T_CLUB)

    def test_loading_sign_is_displayed_before_showing_contents (self):
        view_url = reverse (self.view_path)
        resp = self.client.get (view_url)
        #
        # no table data while loading
        #
        self.assertContains (resp, ugettext ('Loading ...'))
        self.assertContains (resp, 'table class="reservation"', 0)
        #
        # simulate the AJAX request for table data
        #
        resp = self.client.post (view_url,
                                 {'for_date': date.today ( ),},
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains (resp, 'table class="reservation"')


    def test_requested_date_is_included_in_displayed_data (self):
        view_url = reverse (self.view_path)
        rand_date = date.today ( ) + timedelta (days=randint (-10, 10))
        resp = self.client.post (view_url,
                                 {'for_date': rand_date,})
        self.assertEquals (resp.status_code, 200)
        self.assertEquals (resp.template[0].name, self.template_name)
        form = resp.context[-1]['form']
        self.assertEquals (len (form.errors), 0)
        #
        # simulate the AJAX request for table data
        #
        resp = self.client.post (view_url,
                                 {'for_date': rand_date,},
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        displayed_dates = resp.context['week_date_list']
        self.assertTrue (rand_date in displayed_dates)
        self.test_all_active_courts_within_the_active_court_setup_are_displayed (rand_date)


    def test_data_displayed_from_monday_to_sunday (self):
        view_url = reverse (self.view_path)
        for_date = date.today ( )
        #
        # simulate the AJAX request for table data
        #
        resp = self.client.post (view_url,
                                 {'for_date': for_date,},
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        #
        # check that the correct dates are being displayed,
        # for the current week
        #
        for dow in range (1, 8):
            d = for_date + timedelta (days=dow - for_date.isoweekday ( ))
            self.assertContains (resp, d.day)
            self.assertContains (resp, d.month)


    def test_all_active_courts_within_the_active_court_setup_are_displayed (self,
                                                                            for_date=date.today ( )):
        hour_list = Vacancy.HOURS[:-1]
        cs = CourtSetup.objects.get_active (self.club)
        courts = Court.objects.get_available (cs)
        #
        # check that all active courts are being displayed
        #
        view_url = reverse (self.view_path)
        #
        # simulate the AJAX request for table data
        #
        resp = self.client.post (view_url,
                                 {'for_date': for_date,},
                                 HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        for (h, hour) in hour_list:
            for c in courts.iterator ( ):
                v = Vacancy.objects.get (day_of_week=for_date.isoweekday ( ),
                                         available_from=h,
                                         court=c)
                target_address = reverse ('reservations.views.club_edit',
                                          args=[v.id, for_date.toordinal ( )])
                self.assertContains (resp, target_address, 1)


    def test_booked_terms_are_displayed_differently_from_those_free (self):
        print "Not yet implemented!"

    def test_free_is_displayed_on_mouse_over_not_booked_term (self):
        print "Not yet implemented!"

    def test_description_is_displayed_on_mouse_over_booked_reservation (self):
        print "Not yet implemented!"

    def test_click_on_a_term_brings_the_edit_form (self):
        print "Not yet implemented!"

