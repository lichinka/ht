from django.contrib import admin

from reservations.models import Reservation



#
# Register all models in the admin UI
#
admin.site.register (Reservation)