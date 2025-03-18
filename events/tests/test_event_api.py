from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event, Registration
from datetime import datetime, timedelta
from django.utils import timezone


class EventAPITestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='organizer', 
            email='organizer@example.com', 
            password='password123'
        )
        self.attendee = User.objects.create_user(
            username='attendee', 
            email='attendee@example.com', 
            password='password123'
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Test Conference',
            description='A test conference for API testing',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            venue='Test Venue',
            capacity=100,
            organizer=self.organizer
        )
        
        # URLs
        self.events_url = reverse('event-list')
        self.event_detail_url = reverse('event-detail', kwargs={'pk': self.event.pk})
        self.event_register_url = reverse('event-register', kwargs={'pk': self.event.pk})
        self.event_tracks_url = reverse('event-tracks', kwargs={'pk': self.event.pk})
    
    def test_create_event(self):
        """Test creating a new event"""
        self.client.force_authenticate(user=self.organizer)
        data = {
            'title': 'New Test Event',
            'description': 'A new test event created via API',
            'start_date': (timezone.now() + timedelta(days=5)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'venue': 'New Test Venue',
            'capacity': 50
        }
        response = self.client.post(self.events_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 2)
        self.assertEqual(Event.objects.get(title='New Test Event').organizer, self.organizer)
    
    def test_get_events_list(self):
        """Test retrieving a list of events"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.events_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_event_detail(self):
        """Test retrieving a specific event"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Conference')
    
    def test_update_event(self):
        """Test updating an event"""
        self.client.force_authenticate(user=self.organizer)
        data = {'title': 'Updated Test Conference'}
        response = self.client.patch(self.event_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Event.objects.get(pk=self.event.pk).title, 'Updated Test Conference')
    
    def test_delete_event(self):
        """Test deleting an event"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.delete(self.event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 0)
    
    def test_register_for_event(self):
        """Test registering for an event"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.event_register_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Registration.objects.filter(event=self.event, attendee=self.attendee).exists())
    
    def test_register_for_event_already_registered(self):
        """Test registering for an event when already registered"""
        # Create a registration first
        Registration.objects.create(event=self.event, attendee=self.attendee, status='pending')
        
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.event_register_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_for_full_event(self):
        """Test registering for an event that has reached capacity"""
        # Update event to be at capacity
        self.event.capacity = 1
        self.event.save()
        
        # Create a confirmed registration
        Registration.objects.create(
            event=self.event, 
            attendee=User.objects.create_user(username='other_user', password='password123'),
            status='confirmed'
        )
        
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.event_register_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthorized_update(self):
        """Test that non-organizers cannot update events"""
        self.client.force_authenticate(user=self.attendee)
        data = {'title': 'Hacked Event'}
        response = self.client.patch(self.event_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(Event.objects.get(pk=self.event.pk).title, 'Hacked Event')