from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Event, Track, Session, Registration, SessionRegistration
from .serializers import (
    EventSerializer, TrackSerializer, SessionSerializer,
    RegistrationSerializer, SessionRegistrationSerializer
)
from .permissions import IsOrganizerOrReadOnly, IsEventOrganizerOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsOrganizerOrReadOnly, permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['venue', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'venue']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        event = self.get_object()
        
        # Check if user is already registered
        if Registration.objects.filter(event=event, attendee=request.user).exists():
            return Response(
                {'detail': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if event is full
        if event.registrations.filter(status='confirmed').count() >= event.capacity:
            return Response(
                {'detail': 'Event has reached maximum capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration = Registration.objects.create(
            event=event,
            attendee=request.user,
            status='pending'
        )
        
        serializer = RegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        event = self.get_object()
        tracks = event.tracks.all()
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOrganizerOrReadOnly]
    
    def get_queryset(self):
        event_pk = self.kwargs.get('event_pk')
        queryset = Track.objects.all()
        if event_pk:
            queryset = queryset.filter(event__pk=event_pk)
        return queryset
    
    def perform_create(self, serializer):
        event = get_object_or_404(Event, pk=self.kwargs.get('event_pk'))
        if event.organizer != self.request.user:
            self.permission_denied(self.request, message='You are not the organizer of this event')
        serializer.save(event=event)
    
    @action(detail=True, methods=['get', 'post'])
    def sessions(self, request, pk=None, event_pk=None):
        track = self.get_object()
        if request.method == 'GET':
            sessions = track.sessions.all()
            serializer = SessionSerializer(sessions, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            if track.event.organizer != request.user:
                return Response({'detail': 'You are not the organizer of this event.'}, status=status.HTTP_403_FORBIDDEN)
            serializer = SessionSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(track=track)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['start_time', 'end_time']
    ordering_fields = ['start_time', 'end_time']
    
    def get_queryset(self):
        track_pk = self.kwargs.get('track_pk')
        event_pk = self.kwargs.get('event_pk')
        queryset = Session.objects.all()
        
        if track_pk:
            queryset = queryset.filter(track__pk=track_pk)
            if event_pk:
                queryset = queryset.filter(track__event__pk=event_pk)
        
        return queryset.filter(
            Q(track__event__organizer=self.request.user) | 
            Q(track__event__registrations__attendee=self.request.user, 
              track__event__registrations__status='confirmed')
        ).distinct()
    
    def perform_create(self, serializer):
        track_pk = self.kwargs.get('track_pk')
        track = get_object_or_404(Track, pk=track_pk)
        
        if not track:
            self.permission_denied(self.request, message='Invalid track')
        
        if track.event.organizer != self.request.user:
            self.permission_denied(self.request, message='You are not the organizer of this event')
            
        serializer.save(track=track)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None, event_pk=None, track_pk=None):
        session = get_object_or_404(Session, pk=pk)
        
        # Check if user is registered for the event
        if not Registration.objects.filter(
            event=session.track.event, 
            attendee=request.user,
            status='confirmed'
        ).exists():
            return Response(
                {'detail': 'You must be registered for the event first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if session is full
        if session.capacity and session.attendees.count() >= session.capacity:
            return Response(
                {'detail': 'Session has reached maximum capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already registered
        if SessionRegistration.objects.filter(session=session, attendee=request.user).exists():
            return Response(
                {'detail': 'You are already registered for this session.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session_registration = SessionRegistration.objects.create(
            session=session,
            attendee=request.user
        )
        
        serializer = SessionRegistrationSerializer(session_registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'event']
    
    def get_queryset(self):
        if self.action == 'approve':
            return Registration.objects.all()
        user = self.request.user
        if user.is_staff:
            return Registration.objects.all()
        queryset = Registration.objects.filter(
            Q(attendee=user) | Q(event__organizer=user)
        )
        return queryset.order_by('-registration_date')
    
    def perform_create(self, serializer):
        session = get_object_or_404(Session, pk=self.request.data.get('session_id'))
        
        # Check if user is registered for the event
        if not Registration.objects.filter(
            event=session.track.event,
            attendee=self.request.user,
            status='confirmed'
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'You must be registered for the event first.'}
            )
        
        # Check if session is full
        if session.capacity and session.attendees.count() >= session.capacity:
            raise serializers.ValidationError(
                {'detail': 'Session has reached maximum capacity.'}
            )
        
        # Check if already registered
        if SessionRegistration.objects.filter(session=session, attendee=self.request.user).exists():
            raise serializers.ValidationError(
                {'detail': 'You are already registered for this session.'}
            )
        
        serializer.save(attendee=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        registration = self.get_object()
        
        # Check if user is the event organizer
        if registration.event.organizer != request.user:
            return Response(
                {'detail': 'You are not authorized to approve registrations for this event.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if event is full
        if registration.event.registrations.filter(status='confirmed').count() >= registration.event.capacity:
            return Response(
                {'detail': 'Event has reached maximum capacity.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration.status = 'confirmed'
        registration.save()
        
        serializer = self.get_serializer(registration)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        # Get registration without checking permissions first
        registration = Registration.objects.get(pk=pk)
        
        # Check if user is the attendee or event organizer
        if registration.attendee != request.user and registration.event.organizer != request.user:
            return Response(
                {'detail': 'You are not authorized to cancel this registration.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        registration.status = 'cancelled'
        registration.save()
        
        serializer = self.get_serializer(registration)
        return Response(serializer.data)


class SessionRegistrationViewSet(viewsets.ModelViewSet):
    queryset = SessionRegistration.objects.all()
    serializer_class = SessionRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SessionRegistration.objects.all()
        return SessionRegistration.objects.filter(
            Q(attendee=user) | Q(session__track__event__organizer=user)
        )
    
    def perform_create(self, serializer):
        session = get_object_or_404(Session, pk=self.request.data.get('session_id'))
        
        # Check if user is registered for the event
        if not Registration.objects.filter(
            event=session.track.event,
            attendee=self.request.user,
            status='confirmed'
        ).exists():
            raise serializers.ValidationError(
                {'detail': 'You must be registered for the event first.'}
            )
        
        # Check if session is full
        if session.capacity and session.attendees.count() >= session.capacity:
            raise serializers.ValidationError(
                {'detail': 'Session has reached maximum capacity.'}
            )
        
        # Check if already registered
        if SessionRegistration.objects.filter(session=session, attendee=self.request.user).exists():
            raise serializers.ValidationError(
                {'detail': 'You are already registered for this session.'}
            )
        
        serializer.save(attendee=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        session_registration = self.get_object()
        
        # Check if user is the attendee or event organizer
        if (session_registration.attendee != request.user and 
                session_registration.session.track.event.organizer != request.user):
            return Response(
                {'detail': 'You are not authorized to cancel this registration.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session_registration.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)