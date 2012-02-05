from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
from django.core.urlresolvers import reverse

from views import HomeViewTest



class AdvancedTestSuiteRunner (DjangoTestSuiteRunner):
    """
    A custom test suite to avoid running tests of applications
    specified in settings.TEST_EXCLUDE.-
    """
    EXCLUDED_APPS = getattr (settings, 'TEST_EXCLUDE', [])

    def __init__(self, *args, **kwargs):
        super (AdvancedTestSuiteRunner, self).__init__ (*args, **kwargs)

    def build_suite (self, *args, **kwargs):
        suite = super (AdvancedTestSuiteRunner, self).build_suite (*args, **kwargs)
        if not args[0] and not getattr(settings, 'RUN_ALL_TESTS', False):
            tests = []
            for case in suite:
                pkg = case.__class__.__module__.split('.')[0]
                if pkg not in self.EXCLUDED_APPS:
                    tests.append (case)
            suite._tests = tests
        return suite

