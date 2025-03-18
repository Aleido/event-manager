from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event, Track
from datetime import timedelta
from django.utils import timezone


class TrackAPITestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='track_organizer', 
            email='track_organizer@example.com', 
            password='password123'
        )
        self.attendee = User.objects.create_user(
            username='track_attendee', 
            email='track_attendee@example.com', 
            password='password123'
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Track Test Conference',
            description='A test conference for track API testing',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            venue='Track Test Venue',
            capacity=100,
            organizer=self.organizer
        )
        
        # Create test track
        self.track = Track.objects.create(
            event=self.event,
            name='Test Track',
            description='A test track for API testing'
        )
        
        # URLs
        self.tracks_url = reverse('event-tracks-list', kwargs={'event_pk': self.event.pk})
        self.track_detail_url = reverse('event-tracks-detail', 
                                       kwargs={'event_pk': self.event.pk, 'pk': self.track.pk})
        self.track_sessions_url = reverse('event-tracks-sessions', 
                                         kwargs={'event_pk': self.event.pk, 'pk': self.track.pk})
    
    def test_create_track(self):
        """Test creating a new track"""
        self.client.force_authenticate(user=self.organizer)
        data = {
            'name': 'New Test Track',
            'description': 'A new test track created via API'
        }
        response = self.client.post(self.tracks_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Track.objects.count(), 2)
        self.assertEqual(Track.objects.get(name='New Test Track').event, self.event)
    
    def test_get_tracks_list(self):
        """Test retrieving a list of tracks"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.tracks_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_get_track_detail(self):
        """Test retrieving a specific track"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.track_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Track')
    
    def test_update_track(self):
        """Test updating a track"""
        self.client.force_authenticate(user=self.organizer)
        data = {'name': 'Updated Test Track'}
        response = self.client.patch(self.track_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Track.objects.get(pk=self.track.pk).name, 'Updated Test Track')
    
    def test_delete_track(self):
        """Test deleting a track"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.delete(self.track_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Track.objects.count(), 0)
    
    def test_unauthorized_track_creation(self):
        """Test that non-organizers cannot create tracks"""
        self.client.force_authenticate(user=self.attendee)
        data = {
            'name': 'Unauthorized Track',
            'description': 'This track should not be created'
        }
        response = self.client.post(self.tracks_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Track.objects.count(), 1)
    
    def test_unauthorized_track_update(self):
        """Test that non-organizers cannot update tracks"""
        self.client.force_authenticate(user=self.attendee)
        data = {'name': 'Hacked Track'}
        response = self.client.patch(self.track_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(Track.objects.get(pk=self.track.pk).name, 'Hacked Track')