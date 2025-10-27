from django.contrib import admin

from theatre.models import (Actor, Genre, Performance, Play, Reservation,
                            TheatreHall, Ticket)

admin.site.register(TheatreHall)
admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Play)
admin.site.register(Performance)
admin.site.register(Reservation)
admin.site.register(Ticket)
