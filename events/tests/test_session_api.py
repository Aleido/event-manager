from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event, Track, Session, Registration, SessionRegistration
from datetime import timedelta
from django.utils import timezone


class SessionAPITestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='session_organizer', 
            email='session_organizer@example.com', 
            password='password123'
        )
        self.attendee = User.objects.create_user(
            username='session_attendee', 
            email='session_attendee@example.com', 
            password='password123'
        )
        self.speaker = User.objects.create_user(
            username='session_speaker', 
            email='session_speaker@example.com', 
            password='password123'
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Session Test Conference',
            description='A test conference for session API testing',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            venue='Session Test Venue',
            capacity=100,
            organizer=self.organizer
        )
        
        # Create test track
        self.track = Track.objects.create(
            event=self.event,
            name='Session Test Track',
            description='A test track for session API testing'
        )
        
        # Create test session
        self.session = Session.objects.create(
            track=self.track,
            title='Test Session',
            description='A test session for API testing',
            speaker=self.speaker,
            start_time=self.event.start_date + timedelta(hours=1),
            end_time=self.event.start_date + timedelta(hours=2),
            capacity=50
        )
        
        # Create confirmed registration for attendee
        self.registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            status='confirmed'
        )
        
        # URLs
        self.sessions_url = reverse('track-sessions-list', 
                                   kwargs={'event_pk': self.event.pk, 'track_pk': self.track.pk})
        self.session_detail_url = reverse('track-sessions-detail', 
                                         kwargs={'event_pk': self.event.pk, 
                                                'track_pk': self.track.pk, 
                                                'pk': self.session.pk})
        self.session_register_url = reverse('track-sessions-register', 
                                          kwargs={'event_pk': self.event.pk, 
                                                 'track_pk': self.track.pk, 
                                                 'pk': self.session.pk})
    
    def test_create_session(self):
        """Test creating a new session"""
        self.client.force_authenticate(user=self.organizer)
        data = {
            'title': 'New Test Session',
            'description': 'A new test session created via API',
            'speaker_id': self.speaker.id,
            'start_time': (self.event.start_date + timedelta(hours=3)).isoformat(),
            'end_time': (self.event.start_date + timedelta(hours=4)).isoformat(),
            'capacity': 30
        }
        response = self.client.post(self.sessions_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Session.objects.count(), 2)
        self.assertEqual(Session.objects.get(title='New Test Session').track, self.track)
    
    def test_get_sessions_list(self):
        """Test retrieving a list of sessions"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_get_session_detail(self):
        """Test retrieving a specific session"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.session_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Session')
    
    def test_update_session(self):
        """Test updating a session"""
        self.client.force_authenticate(user=self.organizer)
        data = {'title': 'Updated Test Session'}
        response = self.client.patch(self.session_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Session.objects.get(pk=self.session.pk).title, 'Updated Test Session')
    
    def test_delete_session(self):
        """Test deleting a session"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.delete(self.session_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Session.objects.count(), 0)
    
    def test_register_for_session(self):
        """Test registering for a session"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.session_register_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SessionRegistration.objects.filter(
            session=self.session, attendee=self.attendee).exists())
    
    def test_register_for_session_not_registered_for_event(self):
        """Test registering for a session when not registered for the event"""
        # Create a new user who is not registered for the event
        unregistered_user = User.objects.create_user(
            username='unregistered', 
            email='unregistered@example.com', 
            password='password123'
        )
        
        self.client.force_authenticate(user=unregistered_user)
        response = self.client.post(self.session_register_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_for_full_session(self):
        """Test registering for a session that has reached capacity"""
        # Update session to be at capacity
        self.session.capacity = 1
        self.session.save()
        
        # Create a session registration
        SessionRegistration.objects.create(
            session=self.session,
            attendee=User.objects.create_user(username='other_session_user', password='password123')
        )
        
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.session_register_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_for_session_already_registered(self):
        """Test registering for a session when already registered"""
        # Create a session registration first
        SessionRegistration.objects.create(session=self.session, attendee=self.attendee)
        
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.session_register_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthorized_session_creation(self):
        """Test that non-organizers cannot create sessions"""
        self.client.force_authenticate(user=self.attendee)
        data = {
            'title': 'Unauthorized Session',
            'description': 'This session should not be created',
            'speaker_id': self.speaker.id,
            'start_time': (self.event.start_date + timedelta(hours=5)).isoformat(),
            'end_time': (self.event.start_date + timedelta(hours=6)).isoformat(),
            'capacity': 30
        }
        response = self.client.post(self.sessions_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Session.objects.count(), 1)