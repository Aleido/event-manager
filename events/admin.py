from django.contrib import admin
from .models import Event, Track, Session, Registration, SessionRegistration

# Register your models here.
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'venue', 'organizer')
    list_filter = ('start_date', 'venue')
    search_fields = ('title', 'description', 'venue')
    date_hierarchy = 'start_date'

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'description')
    list_filter = ('event',)
    search_fields = ('name', 'description')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'track', 'speaker', 'start_time', 'end_time')
    list_filter = ('track__event', 'track', 'speaker')
    search_fields = ('title', 'description')

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'attendee', 'status', 'registration_date')
    list_filter = ('status', 'event')
    search_fields = ('event__title', 'attendee__username')

@admin.register(SessionRegistration)
class SessionRegistrationAdmin(admin.ModelAdmin):
    list_display = ('session', 'attendee', 'registration_date')
    list_filter = ('session__track__event', 'session')
    search_fields = ('session__title', 'attendee__username')