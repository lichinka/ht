# -*- coding=utf-8 -*-
#
# Django settings for testing the hocemtenis project.
#
from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_luka_ht',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'TEST_NAME': 'test_luka_ht',
    }
}

