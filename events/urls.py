from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    EventViewSet, TrackViewSet, SessionViewSet,
    RegistrationViewSet, SessionRegistrationViewSet
)

router = DefaultRouter()
router.register(r'events', EventViewSet)
router.register(r'registrations', RegistrationViewSet)
router.register(r'session-registrations', SessionRegistrationViewSet, basename='session-registration')

# Nested routes for tracks under events
event_router = routers.NestedDefaultRouter(router, r'events', lookup='event')
event_router.register(r'tracks', TrackViewSet, basename='event-tracks')

# Nested routes for sessions under tracks
track_router = routers.NestedDefaultRouter(event_router, r'tracks', lookup='track')
track_router.register(r'sessions', SessionViewSet, basename='track-sessions')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(event_router.urls)),
    path('', include(track_router.urls)),
]