from fabric.api import *
from fabric.utils import *
from fabric.contrib import project, console

#
# These are our apps within this project.
# We want to run migrations (South) on them.
#
env.apps = ['ht_utils', 'locations', 'accounts', 'wiki', 'players',
            'clubs', 'user_messages', 'ranking', 'comments', 
            'reservations']
#
# Where the project code lives locally
#
env.local_root = '/home/luka/etc/saion/ht_si/env/ht/'

#
# Where the static files live locally
#
env.local_static_root = '%s%s/' % (env.local_root,
                                   'static')
#
# Remote server host to deploy to
#
env.hosts = ['luka@s8.wservices.ch:22']
#
# Where your project code lives on the server
#
env.remote_init = '/home/luka/init/'
#
# Where your project code lives on the server
#
env.remote_root = '/home/luka/ht/'
#
# Directory used to test the site BEFORE switching it to production
#
env.remote_scratch_dir = '/home/luka/scratch/ht/'
#
# Where the static files live on the server
#
env.remote_static_root = '%s%s/' % (env.remote_root,
                                    'static')



def compile_translations ( ):
    """ Compiles the current set of translations into the app.-
    """
    local ("./manage.py compilemessages")


def update_translations ( ):
    """ Updates the message files for further translating.-
    """
    local ("./manage.py makemessages --all")
    

def remote_init_db ( ):
    """ Initializes the database on the server, applying the initial schema migration step.-
    """
    with cd (env.remote_root):
        run ('PYTHONPATH=/home/luka/django-ht:. python manage.py syncdb --noinput')
        for app in env.apps:
            run ('PYTHONPATH=/home/luka/django-ht:. python manage.py migrate %s' % app)

def init_db ( ):
    """ Initializes the database, applying the initial schema migration step.-
    """
    local ("./manage.py syncdb --noinput")
    for app in env.apps:
        local ("./manage.py migrate %s" % app)


def remote_scratch_test (app=''):
    """ Tests the specified application or all if none given. All tests are run in the remote scratch directory.-
    """
    with cd (env.remote_scratch_dir):
        run ('PYTHONPATH=/home/luka/django-ht:. python manage.py test --verbosity=2 --settings=ht.settings_test --failfast %s' % app)


def remote_test ( ):
    """ Executes all tests in the remote production directory.-
    """
    with cd (env.remote_root):
        run ('PYTHONPATH=/home/luka/django-ht:. python manage.py test --verbosity=2 --settings=ht.settings_test --failfast')


def test (app=''):
    """ Executes all tests with the corresponding settings file. Accepts app name as parameter.-
    """
    local ("./manage.py test --verbosity=2 --settings=ht.settings_test --noinput --failfast %s" % app)


def generate_static ( ):
    """ Generates the 'static' directory with all content.-
    """
    local ('./manage.py collectstatic --verbosity=2 --noinput')


def remote_create_scratch_dir ( ):
    with cd ('~'):
        run ('mkdir -p %s' % env.remote_scratch_dir)
        run ('mkdir -p %s/log' % env.remote_scratch_dir)


def deploy_scratch_site ( ):
    """ Deploys the whole site to the server's scratch dir, including static files and translations.-
    """
    generate_static ( )
    compile_translations ( )
    remote_create_scratch_dir ( )
    RSYNC_EXCLUDE = ['.git',
                     '.settings',
                     '.project',
                     '.pydevproject',
                     'staticfiles',
                     'media',
                     'log',
                     '.fabfile.*',
                     'TODO']
    extra_opts = '--omit-dir-times'
    project.rsync_project (
        remote_dir = env.remote_scratch_dir,
        local_dir = env.local_root,
        exclude = RSYNC_EXCLUDE,
        delete = True,
        extra_opts = extra_opts)


def start_server ( ):
    """ Starts the webserver remotely.-
    """
    with cd (env.remote_init):
        run ('./ht start')
        run ('./lighttpd start')


def stop_server ( ):
    """ Stops the webserver remotely.-
    """
    with cd (env.remote_init):
        run ('./lighttpd stop')
        run ('./ht stop')


def remote_switch_dirs ( ):
    """ Changes the scratch directory to production and archives the previous production one.-
    """
    with cd ('~'):
        run ('rm -rf ht_$(date %s)' % '+%Y%m%d')
        run ('mv %s ht_$(date %s)' % (env.remote_root, '+%Y%m%d'))
        run ('mv %(remote_scratch_dir)s %(remote_root)s' % env)


def deploy ( ):
    """ Tests, deploys and restarts the server.-
    """
    if not console.confirm ('Deploy to production?',
                            default=False):
        abort ('Production deployment aborted.')
    else:
        test ( )
        deploy_scratch_site ( )
        remote_scratch_test ( )
        stop_server ( )
        remote_switch_dirs ( )
        start_server ( )
        remote_test ( )

