from django.contrib import admin

from clubs.models import CourtSetup, Court, Vacancy


class CourtSetupAdmin (admin.ModelAdmin):
    list_display = ('club', 'name', 'is_active')
    
class VacancyInline (admin.TabularInline):
    model = Vacancy

class CourtAdmin (admin.ModelAdmin):
    list_display = ('get_club', 
                    'court_setup',
                    'number',
                    'is_available')
    inlines = [VacancyInline,]
    
#
# Register all models in the admin UI
#
admin.site.register (CourtSetup, CourtSetupAdmin)
admin.site.register (Court, CourtAdmin)