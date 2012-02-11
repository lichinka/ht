import locale, random, string

from django.conf import settings
from django.test.client import Client
from django.test.simple import DjangoTestSuiteRunner
from django.test.testcases import TestCase
    
    
    
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
