from django.contrib import admin
from wiki.models import Article

class ArticleAdmin (admin.ModelAdmin):
    """
    Changes the look of the Article model in the admin UI.-
    """
    list_display = ['title', 'text']
    
    

#
# Register all models in the admin UI
#
admin.site.register (Article, ArticleAdmin)