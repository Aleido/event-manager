from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from events.models import Event, Registration
from datetime import timedelta
from django.utils import timezone


class RegistrationAPITestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.organizer = User.objects.create_user(
            username='reg_organizer', 
            email='reg_organizer@example.com', 
            password='password123'
        )
        self.attendee = User.objects.create_user(
            username='reg_attendee', 
            email='reg_attendee@example.com', 
            password='password123'
        )
        self.other_attendee = User.objects.create_user(
            username='other_reg_attendee', 
            email='other_reg_attendee@example.com', 
            password='password123'
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Registration Test Conference',
            description='A test conference for registration API testing',
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now() + timedelta(days=12),
            venue='Registration Test Venue',
            capacity=100,
            organizer=self.organizer
        )
        
        # Create test registration
        self.registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            status='pending',
            notes='Test registration notes'
        )
        
        # URLs
        self.registrations_url = reverse('registration-list')
        self.registration_detail_url = reverse('registration-detail', kwargs={'pk': self.registration.pk})
        self.registration_approve_url = reverse('registration-approve', kwargs={'pk': self.registration.pk})
        self.registration_cancel_url = reverse('registration-cancel', kwargs={'pk': self.registration.pk})
    
    def test_create_registration(self):
        """Test creating a new registration"""
        self.client.force_authenticate(user=self.other_attendee)
        data = {
            'event_id': self.event.id,
            'notes': 'New registration notes'
        }
        response = self.client.post(self.registrations_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Registration.objects.count(), 2)
        self.assertEqual(Registration.objects.get(attendee=self.other_attendee).status, 'pending')
    
    def test_get_registrations_list_as_attendee(self):
        """Test retrieving a list of registrations as an attendee"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.registrations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Attendee should only see their own registrations
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_registrations_list_as_organizer(self):
        """Test retrieving a list of registrations as an organizer"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.get(self.registrations_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Organizer should see registrations for their events
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_registration_detail(self):
        """Test retrieving a specific registration"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.get(self.registration_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notes'], 'Test registration notes')
    
    def test_update_registration(self):
        """Test updating a registration"""
        self.client.force_authenticate(user=self.attendee)
        data = {'notes': 'Updated registration notes'}
        response = self.client.patch(self.registration_detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).notes, 'Updated registration notes')
    
    def test_approve_registration(self):
        """Test approving a registration"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(self.registration_approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).status, 'confirmed')
    
    def test_unauthorized_approve_registration(self):
        """Test that non-organizers cannot approve registrations"""
        self.client.force_authenticate(user=self.other_attendee)
        response = self.client.post(self.registration_approve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).status, 'pending')
    
    def test_approve_registration_for_full_event(self):
        """Test approving a registration when event is at capacity"""
        # Update event to be at capacity
        self.event.capacity = 1
        self.event.save()
        
        # Create a confirmed registration
        Registration.objects.create(
            event=self.event,
            attendee=self.other_attendee,
            status='confirmed'
        )
        
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(self.registration_approve_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).status, 'pending')
    
    def test_cancel_registration_as_attendee(self):
        """Test cancelling a registration as an attendee"""
        self.client.force_authenticate(user=self.attendee)
        response = self.client.post(self.registration_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).status, 'cancelled')
    
    def test_cancel_registration_as_organizer(self):
        """Test cancelling a registration as an organizer"""
        self.client.force_authenticate(user=self.organizer)
        response = self.client.post(self.registration_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).status, 'cancelled')
    
    def test_unauthorized_cancel_registration(self):
        """Test that unauthorized users cannot cancel registrations"""
        self.client.force_authenticate(user=self.other_attendee)
        response = self.client.post(self.registration_cancel_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Registration.objects.get(pk=self.registration.pk).status, 'pending')