from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event, Track, Session, Registration, SessionRegistration
from datetime import timedelta
from django.utils import timezone


class SessionRegistrationAPITestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='session_reg_organizer', 
            email='session_reg_organizer@example.com', 
            password='password123'
        )
        self.attendee = User.objects.create_user(
            username='session_reg_attendee', 
            email='session_reg_attendee@example.com', 
            password='password123'
        )
        self.other_attendee = User.objects.create_user(
            username='other_session_reg_attendee', 
            email='other_session_reg_attendee@example.com', 
            password='password123'
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Session Registration Test Conference',
            description='A test conference for session registration API testing',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            venue='Session Registration Test Venue',
            capacity=100,
            organizer=self.organizer
        )
        
        # Create test track
        self.track = Track.objects.create(
            event=self.event,
            name='Session Registration Test Track',
            description='A test track for session registration API testing'
        )
        
        # Create test session
        self.session = Session.objects.create(
            track=self.track,
            title='Session Registration Test Session',
            description='A test session for session registration API testing',
            start_time=self.event.start_date + timedelta(hours=1),
            end_time=self.event.start_date + timedelta(hours=2),
            capacity=50
        )
        
        # Create confirmed registrations
        self.registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            status='confirmed'
        )
        
        self.other_registration = Registration.objects.create(
            event=self.event,
            attendee=self.other_attendee,
            status='confirmed'
        )
        
        # Create session registration
        self.session_registration = SessionRegistration.objects.create(
            session=self.session,
            attendee=self.attendee
        )
        
        # URLs
        self.session_registrations_url = reverse('session-registration-list')
        self.session_registration_detail_url = reverse(
            'session-registration-detail', 
            kwargs={'pk': self.session_registration.pk}
        )
        self.session_registration_cancel_url = reverse(
            'session-registration-cancel', 
            kwargs={'pk': self.session_registration.pk}
        )
    
    def test_create_session_registration(self):
        """Test creating a new session registration"""
        self.client.force_authenticate(user=self.other_attendee)
        data = {
            'session_id': self.session.id
        }
        response = self.client.post(self.session_registrations_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SessionRegistration.objects.count(), 2)
        self.assertTrue(SessionRegistration.objects.filter(
            session=self.session, attendee=self.other_attendee).exists())
    
    def test_get_session_registrations_list_as_attendee(self):
        """Test retrieving a list of session registrations as an attendee"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.session_registrations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Attendee should only see their own session registrations
        self.assertEqual(len(response.data), 1)
    
    def test_get_session_registrations_list_as_organizer(self):
        """Test retrieving a list of session registrations as an organizer"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(self.session_registrations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Organizer should see session registrations for their events
        self.assertEqual(len(response.data), 1)
    
    def test_get_session_registration_detail(self):
        """Test retrieving a specific session registration"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.session_registration_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session']['title'], 'Session Registration Test Session')
    
    def test_cancel_session_registration_as_attendee(self):
        """Test cancelling a session registration as an attendee"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.session_registration_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SessionRegistration.objects.count(), 0)
    
    def test_cancel_session_registration_as_organizer(self):
        """Test cancelling a session registration as an organizer"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(self.session_registration_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SessionRegistration.objects.count(), 0)
    
    def test_unauthorized_cancel_session_registration(self):
        """Test that unauthorized users cannot cancel session registrations"""
        self.client.force_authenticate(user=self.other_attendee)
        response = self.client.post(self.session_registration_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SessionRegistration.objects.count(), 1)
    
    def test_create_session_registration_not_registered_for_event(self):
        """Test creating a session registration when not registered for the event"""
        # Create a new user who is not registered for the event
        unregistered_user = User.objects.create_user(
            username='unregistered_session_user', 
            email='unregistered_session@example.com', 
            password='password123'
        )
        
        self.client.force_authenticate(user=unregistered_user)
        data = {
            'session_id': self.session.id
        }
        response = self.client.post(self.session_registrations_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SessionRegistration.objects.count(), 1)
    
    def test_create_session_registration_for_full_session(self):
        """Test creating a session registration when session is at capacity"""
        # Update session to be at capacity
        self.session.capacity = 1
        self.session.save()
        
        self.client.force_authenticate(user=self.other_attendee)
        data = {
            'session_id': self.session.id
        }
        response = self.client.post(self.session_registrations_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SessionRegistration.objects.count(), 1)