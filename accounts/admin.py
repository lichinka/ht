from django.contrib import admin

from accounts.models import PlayerProfile, ClubProfile


#
# Register all models in the admin UI
#
admin.site.register (PlayerProfile)
admin.site.register (ClubProfile)