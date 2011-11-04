from players.models import Vacancy
from django.test import TestCase


class VacancyTest(TestCase):
    """
    All tests of the Vacancy model.-
    """
    def test_get_weekdays (self):
        """
        The week days returned should be valid.-
        """
        returned = Vacancy.get_weekdays ( )
        expected = ['MO', 'TU', 'WE', 'TH', 'FR']
        self.assertEqual (returned, expected)

    def test_get_weekends (self):
        """
        The weekend days returned should be valid.-
        """
        returned = Vacancy.get_weekends ( )
        expected = ['SA', 'SU']
        self.assertEqual (returned, expected)
        