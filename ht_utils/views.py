"""
Various helper functions used by different views in the project.-
"""
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.core.urlresolvers import reverse



def get_next_url (request, fallback_url=None):
    """
    Returns the 'next_url' field from the received 'request'.
    If no such field is found, the 'fallback_url' is returned
    (it defaults to the home page).-
    """
    if 'next_url' in request.REQUEST:
        return request.REQUEST['next_url']
    else:
        if fallback_url is None:
            fallback_url = reverse ('home')
        return fallback_url
    
    
        
def success (request, title=None, body=None, template_name='ht_utils/success.html'):
    """
    Displays a success page with the received content.-
    """
    return render_to_response (template_name,
                               {'title': title,
                                'body': body},
                               context_instance=RequestContext(request))
