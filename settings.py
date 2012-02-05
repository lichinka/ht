# -*- coding=utf-8 -*-
#
# Django settings for hocemtenis project.
#
import os.path

BASE_PATH = os.path.dirname(__file__)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SERVER_EMAIL = 'webmaster@hocemtenis.si'

ADMINS = (
    (u'Lucas Benedicic', 'lucas.benedicic@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'luka_ht',
        'USER': 'luka',
        'PASSWORD': 'yOExvQ5J',
        'HOST': '',
        'PORT': '',
        'TEST_NAME': 'test_luka_ht',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Ljubljana'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'sl'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = BASE_PATH + '/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = BASE_PATH + '/static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    BASE_PATH + '/staticfiles/',
    MEDIA_ROOT,
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '%d%(rxe1x7s5(3@f99d!6k5p(&amp;o#$i%_oll3x6tp8(+2&amp;h6g5-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
#    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
#    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'ht.urls'
LOGIN_URL = '/accounts/login'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    BASE_PATH + '/templates',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.markup',        # Enables wiki-like parsing and HTML rendering
    'django.contrib.staticfiles',   # Enables serving static files during development
    'template_repl',                # Enables interactive debugging of templates during development
    'south',             # Eases model-to-database synchronization.
                         # For inter-app dependency, the order defined here matters!
    'locations',         # Enables location-lookups via cities and coordinates
    'actstream',         # Feed-based tracking of user's activity
    'accounts',          # Includes user's profile
    'wiki',              # Wiki module of the site
    'players',           # Help people find other players for playing tennis
    'clubs',             # Keeps clubs data and profiles
    'user_messages',     # Lets users send private messages to each other
    'ranking',           # Keeps all match results and a players' ranking
    'comments',          # Enables model-based comments with images
    'reservations',      # An application to enable users to book courts and let the clubs run their reservations via web
    'ht_utils',          # Various utility functions used everywhere
    # Uncomment the next line to enable the admin:
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# Override the server-derived value of SCRIPT_NAME
# See http://code.djangoproject.com/wiki/BackwardsIncompatibleChanges#lighttpdfastcgiandothers
FORCE_SCRIPT_NAME = ''

#
# User's activity stream configuration (actstream)
#
ACTSTREAM_ACTION_MODELS = ['auth.User',
                           'accounts.ClubProfile', 'accounts.PlayerProfile',
                           'reservations.Reservation']
ACTSTREAM_ACTION_TEMPLATE = 'activity/single_action.txt'
ACTSTREAM_MANAGER = 'actstream.managers.ActionManager'

#
# Synchronize Python locale with Django settings
#
import locale

mylocale = 'en_US'
if (LANGUAGE_CODE == 'en'):
    mylocale = 'en_US'
elif (LANGUAGE_CODE == 'es'):
    mylocale = 'es_AR'
elif (LANGUAGE_CODE == 'sl'):
    mylocale = 'sl_SI'

locale.setlocale (locale.LC_ALL, (mylocale, 'UTF-8'))


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': BASE_PATH + '/log/app.log',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },
        'request_handler': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': BASE_PATH + '/log/app_request.log',
                'maxBytes': 1024*1024*5, # 5 MB
                'backupCount': 5,
                'formatter':'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': { # Stop SQL debug from logging to main logger
            'handlers': ['request_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}
