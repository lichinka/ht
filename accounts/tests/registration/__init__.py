from django.test import TestCase

#
# Tests correct integration with the third-party application 'django-registration'.-
#
from registration.tests.backends import *
from registration.tests.forms import *
from registration.tests.models import *

#
# Our version of the views test cases, connected with 'django-registration'.-
#
from views import *
