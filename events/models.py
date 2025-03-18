from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('End date must be after start date')
        if self.start_date and self.start_date < timezone.now():
            raise ValidationError('Start date cannot be in the past')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-start_date']
        permissions = [
            ('view_event_details', 'Can view event details'),
            ('manage_event', 'Can manage event'),
        ]

class Track(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tracks')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f'{self.name} - {self.event.title}'

    class Meta:
        unique_together = ['event', 'name']

class Session(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    speaker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='speaking_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(null=True, blank=True)

    def clean(self):
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValidationError('End time must be after start time')
        if self.start_time < self.track.event.start_date or self.end_time > self.track.event.end_date:
            raise ValidationError('Session must be within event duration')
        
        # Check for scheduling conflicts within the same track
        overlapping_sessions = Session.objects.filter(
            track=self.track,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)
        
        if overlapping_sessions.exists():
            raise ValidationError('Session time conflicts with another session in the same track')

    def __str__(self):
        return f'{self.title} - {self.track.event.title}'

    class Meta:
        ordering = ['start_time']

class Registration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    attendee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def clean(self):
        # Check if event is full
        if self.status == 'confirmed' and self.event.registrations.filter(status='confirmed').count() >= self.event.capacity:
            raise ValidationError('Event has reached maximum capacity')
        
        # Check for duplicate registrations
        if Registration.objects.filter(event=self.event, attendee=self.attendee).exclude(pk=self.pk).exists():
            raise ValidationError('Attendee is already registered for this event')

    def __str__(self):
        return f'{self.attendee.username} - {self.event.title}'

    class Meta:
        unique_together = ['event', 'attendee']
        permissions = [
            ('approve_registration', 'Can approve registration'),
            ('cancel_registration', 'Can cancel registration'),
        ]

class SessionRegistration(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendees')
    attendee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_registrations')
    registration_date = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Check if attendee is registered for the event
        if not Registration.objects.filter(
            event=self.session.track.event,
            attendee=self.attendee,
            status='confirmed'
        ).exists():
            raise ValidationError('Attendee must be registered for the event first')

        # Check session capacity
        if self.session.capacity and self.session.attendees.count() >= self.session.capacity:
            raise ValidationError('Session has reached maximum capacity')

    def __str__(self):
        return f'{self.attendee.username} - {self.session.title}'

    class Meta:
        unique_together = ['session', 'attendee']