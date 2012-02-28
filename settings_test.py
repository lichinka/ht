# -*- coding=utf-8 -*-
#
# Django settings for testing the HT project.
#
from ht.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',              # An in-memory database to speed the tests up.
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

#
# use our custom test suite runner, that supports excluding apps
#
TEST_RUNNER="ht_utils.tests.AdvancedTestSuiteRunner"

#
# we assume all apps belonging to the Django package, including the
# third-party apps used, work correctly. Therefore there is no need
# to run their built-in tests along with ours.
#
TEST_EXCLUDE=('django', 'registration')

#
# do not run South migrations, nor their
# built-in tests during our testing
#
SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True

#
# User's activity stream configuration (actstream)
# for the tests cases not to fail
#
for extra_model in ['auth.Group', 'sites.Site']:
    ACTSTREAM_ACTION_MODELS.append (extra_model)
