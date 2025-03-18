from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event, Track, Session, Registration, SessionRegistration
from datetime import timedelta
from django.utils import timezone


class EventManagementIntegrationTestCase(APITestCase):
    """Integration tests for the complete event management flow"""
    
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='integration_organizer', 
            email='integration_organizer@example.com', 
            password='password123'
        )
        self.attendee1 = User.objects.create_user(
            username='integration_attendee1', 
            email='integration_attendee1@example.com', 
            password='password123'
        )
        self.attendee2 = User.objects.create_user(
            username='integration_attendee2', 
            email='integration_attendee2@example.com', 
            password='password123'
        )
        self.speaker = User.objects.create_user(
            username='integration_speaker', 
            email='integration_speaker@example.com', 
            password='password123'
        )
    
    def test_complete_event_flow(self):
        """Test the complete flow of creating and managing an event"""
        # Step 1: Create an event
        self.client.force_authenticate(user=self.organizer)
        event_data = {
            'title': 'Integration Test Conference',
            'description': 'A conference for testing the complete flow',
            'start_date': (timezone.now() + timedelta(days=30)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=32)).isoformat(),
            'venue': 'Integration Test Venue',
            'capacity': 50
        }
        response = self.client.post(reverse('event-list'), event_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event_id = response.data['id']
        
        # Step 2: Create tracks for the event
        tracks_url = reverse('event-tracks-list', kwargs={'event_pk': event_id})
        track1_data = {
            'name': 'Technical Track',
            'description': 'Technical sessions for developers'
        }
        track2_data = {
            'name': 'Business Track',
            'description': 'Business and management sessions'
        }
        response1 = self.client.post(tracks_url, track1_data, format='json')
        response2 = self.client.post(tracks_url, track2_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        track1_id = response1.data['id']
        track2_id = response2.data['id']
        
        # Step 3: Create sessions for each track
        sessions_url1 = reverse('track-sessions-list', 
                              kwargs={'event_pk': event_id, 'track_pk': track1_id})
        sessions_url2 = reverse('track-sessions-list', 
                              kwargs={'event_pk': event_id, 'track_pk': track2_id})
        
        event_start = timezone.now() + timedelta(days=30)
        session1_data = {
            'title': 'Advanced Django',
            'description': 'Advanced Django techniques',
            'speaker_id': self.speaker.id,
            'start_time': (event_start + timedelta(hours=1)).isoformat(),
            'end_time': (event_start + timedelta(hours=3)).isoformat(),
            'capacity': 30
        }
        session2_data = {
            'title': 'Business Strategy',
            'description': 'Business strategy for tech companies',
            'speaker_id': self.speaker.id,
            'start_time': (event_start + timedelta(hours=4)).isoformat(),
            'end_time': (event_start + timedelta(hours=6)).isoformat(),
            'capacity': 20
        }
        
        response1 = self.client.post(sessions_url1, session1_data, format='json')
        response2 = self.client.post(sessions_url2, session2_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        session1_id = response1.data['id']
        session2_id = response2.data['id']
        
        # Step 4: Attendees register for the event
        self.client.force_authenticate(user=self.attendee1)
        register_url = reverse('event-register', kwargs={'pk': event_id})
        response = self.client.post(register_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        registration1_id = response.data['id']
        
        self.client.force_authenticate(user=self.attendee2)
        response = self.client.post(register_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        registration2_id = response.data['id']
        
        # Step 5: Organizer approves registrations
        self.client.force_authenticate(user=self.organizer)
        approve_url1 = reverse('registration-approve', kwargs={'pk': registration1_id})
        approve_url2 = reverse('registration-approve', kwargs={'pk': registration2_id})
        response1 = self.client.post(approve_url1)
        response2 = self.client.post(approve_url2)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['status'], 'confirmed')
        self.assertEqual(response2.data['status'], 'confirmed')
        
        # Step 6: Attendees register for sessions
        self.client.force_authenticate(user=self.attendee1)
        session1_register_url = reverse('track-sessions-register', 
                                      kwargs={'event_pk': event_id, 
                                             'track_pk': track1_id, 
                                             'pk': session1_id})
        response = self.client.post(session1_register_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_registration1_id = response.data['id']
        
        self.client.force_authenticate(user=self.attendee2)
        session2_register_url = reverse('track-sessions-register', 
                                      kwargs={'event_pk': event_id, 
                                             'track_pk': track2_id, 
                                             'pk': session2_id})
        response = self.client.post(session2_register_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        session_registration2_id = response.data['id']
        
        # Step 7: Verify registrations
        self.client.force_authenticate(user=self.organizer)
        event_detail_url = reverse('event-detail', kwargs={'pk': event_id})
        response = self.client.get(event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_count'], 2)
        
        # Step 8: Attendee cancels session registration
        self.client.force_authenticate(user=self.attendee1)
        cancel_session_url = reverse('session-registration-cancel', 
                                   kwargs={'pk': session_registration1_id})
        response = self.client.post(cancel_session_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Step 9: Attendee cancels event registration
        cancel_registration_url = reverse('registration-cancel', 
                                        kwargs={'pk': registration1_id})
        response = self.client.post(cancel_registration_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'cancelled')
        
        # Step 10: Verify final state
        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(event_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_count'], 1)


class EventCapacityIntegrationTestCase(APITestCase):
    """Integration tests for event capacity management"""
    
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='capacity_organizer', 
            email='capacity_organizer@example.com', 
            password='password123'
        )
        self.attendees = []
        for i in range(5):  # Create 5 attendees
            attendee = User.objects.create_user(
                username=f'capacity_attendee{i}', 
                email=f'capacity_attendee{i}@example.com', 
                password='password123'
            )
            self.attendees.append(attendee)
        
        # Create test event with limited capacity
        self.event = Event.objects.create(
            title='Limited Capacity Conference',
            description='A conference with limited capacity',
            start_date=timezone.now() + timedelta(days=20),
            end_date=timezone.now() + timedelta(days=22),
            venue='Capacity Test Venue',
            capacity=3,  # Only 3 spots available
            organizer=self.organizer
        )
        
        # Create a track
        self.track = Track.objects.create(
            event=self.event,
            name='Capacity Test Track',
            description='Track for capacity testing'
        )
        
        # Create a session with limited capacity
        self.session = Session.objects.create(
            track=self.track,
            title='Limited Capacity Session',
            description='Session with limited capacity',
            start_time=self.event.start_date + timedelta(hours=2),
            end_time=self.event.start_date + timedelta(hours=4),
            capacity=2  # Only 2 spots available
        )
    
    def test_event_capacity_management(self):
        """Test that event capacity limits are enforced"""
        # Step 1: All attendees register for the event
        registrations = []
        for attendee in self.attendees:
            self.client.force_authenticate(user=attendee)
            response = self.client.post(reverse('event-register', kwargs={'pk': self.event.pk}))
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            registrations.append(response.data['id'])
        
        # Step 2: Organizer approves first 3 registrations
        self.client.force_authenticate(user=self.organizer)
        for i in range(3):
            response = self.client.post(reverse('registration-approve', kwargs={'pk': registrations[i]}))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'confirmed')
        
        # Step 3: Organizer tries to approve 4th registration (should fail due to capacity)
        response = self.client.post(reverse('registration-approve', kwargs={'pk': registrations[3]}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Step 4: First 2 confirmed attendees register for the session
        for i in range(2):
            self.client.force_authenticate(user=self.attendees[i])
            session_register_url = reverse('track-sessions-register', 
                                         kwargs={'event_pk': self.event.pk, 
                                                'track_pk': self.track.pk, 
                                                'pk': self.session.pk})
            response = self.client.post(session_register_url)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 5: Third confirmed attendee tries to register for the session (should fail due to capacity)
        self.client.force_authenticate(user=self.attendees[2])
        session_register_url = reverse('track-sessions-register', 
                                     kwargs={'event_pk': self.event.pk, 
                                            'track_pk': self.track.pk, 
                                            'pk': self.session.pk})
        response = self.client.post(session_register_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Step 6: Verify event registration count
        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(reverse('event-detail', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_count'], 3)
        
        # Step 7: Verify session registration count
        session_attendees = SessionRegistration.objects.filter(session=self.session).count()
        self.assertEqual(session_attendees, 2)