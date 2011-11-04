from wiki.models import Article
from wiki.forms import EditArticleForm

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext




def preview (request, article_id = -1):
    """
    Displays the HTML representation of an article markup.-
    """
    a = get_object_or_404 (Article, pk=article_id)
    return render_to_response ('wiki/preview.html',
                               {'article': a})
    
    
def edit (request, article_id = -1):
    """
    Display the form for changing the article content.-
    """
    if (request.method == 'POST'):
        if ('preview' in request.POST):
            #
            # User wants to preview the article before saving it
            #
            form = EditArticleForm (request.POST)
            if (form.is_valid ( )):
                form.save (commit=False)
                return render_to_response ('wiki/preview.html',
                                           {'article': form.instance},
                                           context_instance=RequestContext(request))
        elif ('save' in request.POST):
            #
            # User wants to save the edited article
            #
            pass
    else:
        #
        # An empty form
        #
        form = EditArticleForm ( )
        
    return render_to_response ('wiki/edit.html',
                               {'form': form},
                               context_instance=RequestContext(request))
    
    
def save (request):
    """
    Saves an article in the wiki.-
    """
    pass

    
def index (request):
    """
    Wiki entry point should display the 'Welcome' article.-
    """
    try:
        a = Article.objects.get (title="HT Wiki")
        return preview (request, a.id)
    except ObjectDoesNotExist:
        return preview (request, -1)
    
    
    