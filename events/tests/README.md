# Event Management System Integration Tests Documentation

This document provides detailed information about the integration tests for the Event Management System API. These tests verify that the different components of the system work together correctly and that the business logic is properly implemented.

## Overview

The integration tests are designed to validate the complete flow of event management operations, from event creation to attendee registration and session management. They ensure that:

1. Events can be created, updated, and managed by organizers
2. Tracks and sessions can be created within events
3. Attendees can register for events and sessions
4. Capacity limits are properly enforced at both event and session levels
5. Registration approval and cancellation workflows function correctly

## Test Structure

The integration tests are organized into two main test cases:

1. `EventManagementIntegrationTestCase` - Tests the complete event management flow
2. `EventCapacityIntegrationTestCase` - Tests capacity management for events and sessions

### Test Setup

Both test cases use Django's `APITestCase` class and set up test data in their respective `setUp` methods:

- Test users (organizers, attendees, speakers)
- Test events with specified capacities
- Test tracks and sessions

## Complete Event Flow Test

The `test_complete_event_flow` method in `EventManagementIntegrationTestCase` tests the entire lifecycle of an event, from creation to attendee management. It follows these steps:

1. **Event Creation**: An organizer creates a new event with title, description, dates, venue, and capacity.
2. **Track Creation**: The organizer creates multiple tracks for the event (Technical and Business tracks).
3. **Session Creation**: The organizer creates sessions within each track, specifying speakers, times, and capacities.
4. **Event Registration**: Attendees register for the event, creating pending registrations.
5. **Registration Approval**: The organizer approves attendee registrations, changing their status to "confirmed".
6. **Session Registration**: Confirmed attendees register for specific sessions within tracks.
7. **Registration Verification**: The system verifies the correct number of registrations for the event.
8. **Session Cancellation**: An attendee cancels their session registration.
9. **Event Registration Cancellation**: An attendee cancels their event registration.
10. **Final State Verification**: The system verifies the final state of registrations after cancellations.

This test ensures that the complete flow works correctly and that the system maintains data integrity throughout the process.

## Capacity Management Test

The `test_event_capacity_management` method in `EventCapacityIntegrationTestCase` specifically tests that capacity limits are properly enforced. It follows these steps:

1. **Multiple Registrations**: Five attendees register for an event with a capacity of 3.
2. **Limited Approvals**: The organizer approves the first 3 registrations.
3. **Capacity Enforcement (Event)**: The system prevents the organizer from approving a 4th registration due to capacity limits.
4. **Session Registration**: The first 2 confirmed attendees register for a session with capacity of 2.
5. **Capacity Enforcement (Session)**: The system prevents the 3rd confirmed attendee from registering for the session due to capacity limits.
6. **Verification**: The system verifies the correct number of registrations for both the event and session.

This test ensures that capacity limits are properly enforced at both the event and session levels.

## Running the Tests

To run the integration tests, use the following command from the project root directory:

```bash
python manage.py test events.tests.test_integration
```

To run a specific test case:

```bash
python manage.py test events.tests.test_integration.EventManagementIntegrationTestCase
```

To run a specific test method:

```bash
python manage.py test events.tests.test_integration.EventManagementIntegrationTestCase.test_complete_event_flow
```

## Test Dependencies

The integration tests depend on the following models:

- `Event`: Represents an event with title, description, dates, venue, and capacity
- `Track`: Represents a track within an event (e.g., Technical, Business)
- `Session`: Represents a session within a track with speaker, times, and capacity
- `Registration`: Represents an attendee's registration for an event with status (pending, confirmed, cancelled)
- `SessionRegistration`: Represents an attendee's registration for a specific session

## API Endpoints Tested

The integration tests cover the following API endpoints:

- `/events/` - Create and list events
- `/events/{id}/` - Retrieve, update, and delete events
- `/events/{id}/register/` - Register for an event
- `/events/{id}/tracks/` - Create and list tracks for an event
- `/events/{id}/tracks/{id}/sessions/` - Create and list sessions for a track
- `/events/{id}/tracks/{id}/sessions/{id}/register/` - Register for a session
- `/registrations/{id}/approve/` - Approve an event registration
- `/registrations/{id}/cancel/` - Cancel an event registration
- `/session-registrations/{id}/cancel/` - Cancel a session registration

## Validation Rules Tested

The integration tests verify the following validation rules:

1. Event capacity cannot be exceeded
2. Session capacity cannot be exceeded
3. Attendees must be registered for an event before registering for sessions
4. Only organizers can approve registrations
5. Attendees can cancel their own registrations
6. Organizers can cancel any registration

## Extending the Tests

When adding new features to the Event Management System, consider extending these integration tests to cover the new functionality. Some guidelines:

1. Add new test methods to the existing test cases if they fit the current scope
2. Create new test cases for entirely new features or workflows
3. Follow the pattern of setting up test data, performing actions, and verifying results
4. Ensure that both positive scenarios (things working correctly) and negative scenarios (proper error handling) are tested

## Common Issues

- **Test Isolation**: Each test should be independent and not rely on data created by other tests
- **Time-Dependent Tests**: Be careful with tests that depend on specific dates or times
- **Database State**: Tests should clean up after themselves to avoid affecting other tests

## Conclusion

These integration tests provide confidence that the Event Management System works correctly as a whole. They verify that the different components interact properly and that the business rules are correctly implemented.