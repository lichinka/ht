# -*- coding=utf-8 -*-
#
# Django settings for testing the HT project.
#
from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
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
# we assume all apps belonging to the Django package 
# work correctly, therefore there is no need to run 
# their built-in tests every time
#
TEST_EXCLUDE=('django')

#
# do not run South migrations, nor their 
# built-in tests during our testing
#
SOUTH_TESTS_MIGRATE = False
SKIP_SOUTH_TESTS = True
