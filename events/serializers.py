from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, Track, Session, Registration, SessionRegistration


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class SessionSerializer(serializers.ModelSerializer):
    speaker = UserSerializer(read_only=True)
    speaker_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='speaker',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Session
        fields = ['id', 'title', 'description', 'speaker', 'speaker_id', 
                  'start_time', 'end_time', 'capacity', 'track']
        read_only_fields = ['track']


class TrackSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Track
        fields = ['id', 'name', 'description', 'event', 'sessions']
        read_only_fields = ['event']


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    tracks = TrackSerializer(many=True, read_only=True)
    registration_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 
                  'venue', 'capacity', 'organizer', 'tracks', 'registration_count',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_registration_count(self, obj):
        return obj.registrations.filter(status='confirmed').count()


class RegistrationSerializer(serializers.ModelSerializer):
    attendee = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        source='event',
        write_only=True
    )
    
    class Meta:
        model = Registration
        fields = ['id', 'event', 'event_id', 'attendee', 'status', 
                  'registration_date', 'notes']
        read_only_fields = ['registration_date']


class SessionRegistrationSerializer(serializers.ModelSerializer):
    attendee = UserSerializer(read_only=True)
    session = SessionSerializer(read_only=True)
    session_id = serializers.PrimaryKeyRelatedField(
        queryset=Session.objects.all(),
        source='session',
        write_only=True
    )
    
    class Meta:
        model = SessionRegistration
        fields = ['id', 'session', 'session_id', 'attendee', 'registration_date']
        read_only_fields = ['registration_date']