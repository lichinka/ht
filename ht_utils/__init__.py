import locale, random, string

from django.db import transaction
from django.test.simple import DjangoTestSuiteRunner, dependency_ordered



class HtTestSuiteRunner (DjangoTestSuiteRunner):
    """
    FIXME: Not currently used!
    A custom test runner to avoid DB creation/deletion.-
    """
    def setup_databases(self, **kwargs):
        """
        Code adapted from django/test/simple.py
        """
        from django.db import connections, DEFAULT_DB_ALIAS

        # First pass -- work out which databases actually need to be created,
        # and which ones are test mirrors or duplicate entries in DATABASES
        mirrored_aliases = {}
        test_databases = {}
        dependencies = {}
        for alias in connections:
            connection = connections[alias]
            if connection.settings_dict['TEST_MIRROR']:
                # If the database is marked as a test mirror, save
                # the alias.
                mirrored_aliases[alias] = connection.settings_dict['TEST_MIRROR']
            else:
                # Store a tuple with DB parameters that uniquely identify it.
                # If we have two aliases with the same values for that tuple,
                # we only need to create the test database once.
                item = test_databases.setdefault(
                    connection.creation.test_db_signature(),
                    (connection.settings_dict['NAME'], [])
                )
                item[1].append(alias)

                if 'TEST_DEPENDENCIES' in connection.settings_dict:
                    dependencies[alias] = connection.settings_dict['TEST_DEPENDENCIES']
                else:
                    if alias != DEFAULT_DB_ALIAS:
                        dependencies[alias] = connection.settings_dict.get('TEST_DEPENDENCIES', [DEFAULT_DB_ALIAS])

        # Second pass -- actually create the databases.
        old_names = []
        mirrors = []
        for signature, (db_name, aliases) in dependency_ordered(test_databases.items(), dependencies):
            # Actually create the database for the first connection
            connection = connections[aliases[0]]
            old_names.append((connection, db_name, True))
            #test_db_name = connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)
            if connection.settings_dict.get('TEST_NAME'):
                test_db_name = connection.settings_dict.get('TEST_NAME')
            else:
                test_db_name = 'test_%s' % connection.settings_dict.get('NAME')
            for alias in aliases[1:]:
                connection = connections[alias]
                if db_name:
                    old_names.append((connection, db_name, False))
                    connection.settings_dict['NAME'] = test_db_name
                else:
                    # If settings_dict['NAME'] isn't defined, we have a backend where
                    # the name isn't important -- e.g., SQLite, which uses :memory:.
                    # Force create the database instead of assuming it's a duplicate.
                    old_names.append((connection, db_name, True))
                    connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)

        for alias, mirror_alias in mirrored_aliases.items():
            mirrors.append((alias, connections[alias].settings_dict['NAME']))
            connections[alias].settings_dict['NAME'] = connections[mirror_alias].settings_dict['NAME']

        return old_names, mirrors
    
    
    
def random_ascii_string (length):
    """
    Generates a random ASCII-coded string.-
    """
    if length < 200:
        return ''.join (random.choice (string.letters + string.digits) for i in xrange(length))
    else:
        raise ValueError ('Use length values no greater than 200')
    
    

def number_to_default_locale (num):
    """
    Converts a number from the current locale to the C-like form.-
    """
    decimal_sep = locale.nl_langinfo (locale.RADIXCHAR)
    return num.replace (decimal_sep, '.') if decimal_sep in num else num



# Bulk insert/update DB operations for the Django ORM. Useful when
# inserting/updating lots of objects where the bottleneck is overhead
# in talking to the database. Instead of doing this
#
#   for x in seq:
#       o = SomeObject()
#       o.foo = x
#       o.save()
#
# or equivalently this
#
#   for x in seq:
#       SomeObject.objects.create(foo=x)
#
# do this
#
#   l = []
#   for x in seq:
#       o = SomeObject()
#       o.foo = x
#       l.append(o)
#   insert_many(l)
#
# Note that these operations are really simple. They won't work with
# many-to-many relationships, and you may have to divide really big
# lists into smaller chunks before sending them through.
#
# History
# 2010-12-10: quote column names, reported by Beres Botond. 
#
def insert_many (objects, using='default'):
    """
    Insert list of Django objects in one SQL query. Objects must be
    of the same Django model. Note that save is not called and signals
    on the model are not raised.
    """
    if not objects:
        return

    import django.db.models
    from django.db import connections
   
    with transaction.commit_manually (using):
        try:
            con = connections[using]
            
            model = objects[0].__class__
            fields = [f for f in model._meta.fields if not isinstance(f, django.db.models.AutoField)]
            parameters = []
            for o in objects:
                parameters.append(tuple(f.get_db_prep_save(f.pre_save(o, True), connection=con) for f in fields))
        
            table = model._meta.db_table
            column_names = ",".join(con.ops.quote_name(f.column) for f in fields)
            placeholders = ",".join(("%s",) * len(fields))
            
            con.cursor().executemany(
                "insert into %s (%s) values (%s)" % (table, column_names, placeholders),
                parameters)
            transaction.commit (using)

        except:
            transaction.rollback (using)



def update_many(objects, fields=[], using="default"):
    """
    Update list of Django objects in one SQL query, optionally only
    overwrite the given fields (as names, e.g. fields=["foo"]).
    Objects must be of the same Django model. Note that save is not
    called and signals on the model are not raised.
    """
    if not objects:
        return

    import django.db.models
    from django.db import connections

    with transaction.commit_manually (using):
        try:
            con = connections[using]
        
            names = fields
            meta = objects[0]._meta
            fields = [f for f in meta.fields if not isinstance(f, django.db.models.AutoField) and (not names or f.name in names)]
        
            if not fields:
                raise ValueError("No fields to update, field names are %s." % names)
            
            fields_with_pk = fields + [meta.pk]
            parameters = []
            for o in objects:
                parameters.append(tuple(f.get_db_prep_save(f.pre_save(o, True), connection=con) for f in fields_with_pk))
        
            table = meta.db_table
            assignments = ",".join(("%s=%%s"% con.ops.quote_name(f.column)) for f in fields)
            con.cursor().executemany(
                "update %s set %s where %s=%%s" % (table, assignments, con.ops.quote_name(meta.pk.column)),
                parameters)
            transaction.commit (using)

        except:
            transaction.rollback (using)

