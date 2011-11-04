from django.contrib import admin
from players.models import Vacancy, City



class VacancyAdmin (admin.ModelAdmin):
    """
    Changes the look of the Vacancy model in the admin UI.-
    """
    pass
    
    

#
# Register all models in the admin UI
#
admin.site.register (City)
admin.site.register (Vacancy, VacancyAdmin)