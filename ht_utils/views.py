from django.shortcuts import render_to_response
from django.template.context import RequestContext


    
def success (request, title=None, body=None, template_name='ht_utils/success.html'):
    """
    Displays a success page with the received content.-
    """
    return render_to_response (template_name,
                               {'title': title,
                                'body': body},
                               context_instance=RequestContext(request))
