import locale, random, string

from django.db import transaction
from django.conf import settings
from django.test.client import Client
from django.test.simple import DjangoTestSuiteRunner
from django.test.testcases import TestCase
from django.contrib.auth.models import User



def pick_random_element (list):
    """
    Returns a random element from the received list.-
    """
    idx = random.randint (1, len(list))
    return list[idx - 1]


def random_id_list (id_dict, length=None):
    """
    Returns a shuffled list of length 'length' of randomly selected IDs
    from the 'id_dict' received. 'id_dict' can be generated with .values('id').-
    """
    ret_value = [e['id'] for e in id_dict]
    random.shuffle (ret_value)
    if (length > 0) and not (len(ret_value) < length):
        ret_value = ret_value[:length]
    return ret_value

     
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

