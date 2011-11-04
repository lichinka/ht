from fabric.api import *
from fabric.contrib import project, console

#
# Apps within this project
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
# Where the static files live on the server
#
env.remote_static_root = '%s%s/' % (env.remote_root,
                                    'static')



def init_db ( ):
    """ Initializes the database, aplying the initial schema migration step.-
    """
    local ("./manage.py syncdb --noinput")
    for app in env.apps:
        local ("./manage.py migrate %s" % app)


def remote_test ( ):
    """ Executes all tests remotely.-
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


def deploy_site ( ):
    """ Deploys the whole site to the server.-
    """
    generate_static ( )
    RSYNC_EXCLUDE = ['.settings',
                     '.project',
                     '.pydevproject',
                     'staticfiles',
                     'media',
                     'log',
                     '.fabfile.*',
                     'fabfile.*',
                     'TODO']
    extra_opts = '--omit-dir-times'
    project.rsync_project (
        remote_dir = env.remote_root,
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


def deploy ( ):
    """ Tests, deploys and restarts the server.-
    """
    if not console.confirm ('Deploy to production?',
                            default=False):
        utils.abort ('Production deployment aborted.')
    else:
        test ( )
        stop_server ( )
        deploy_site ( )
        remote_test ( )
        start_server ( )

