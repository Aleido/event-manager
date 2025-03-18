# Event Management System API Documentation

This document provides detailed information about the Event Management System API endpoints, request/response formats, authentication requirements, and example usage.

## Authentication

All API endpoints require authentication using JSON Web Tokens (JWT). Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### Event Management

#### List Events
- **GET** `/events/`
- **Description**: Retrieve a list of all events
- **Query Parameters**:
  - `page`: Page number for pagination
  - `page_size`: Number of items per page
  - `search`: Search events by title or description
- **Response**:
```json
{
    "count": 10,
    "next": "http://api.example.com/events/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Tech Conference 2024",
            "description": "Annual technology conference",
            "start_date": "2024-06-01T09:00:00Z",
            "end_date": "2024-06-03T17:00:00Z",
            "venue": "Convention Center",
            "capacity": 500,
            "organizer": {
                "id": 1,
                "username": "org_user"
            }
        }
    ]
}
```

#### Create Event
- **POST** `/events/`
- **Description**: Create a new event
- **Request Body**:
```json
{
    "title": "Tech Conference 2024",
    "description": "Annual technology conference",
    "start_date": "2024-06-01T09:00:00Z",
    "end_date": "2024-06-03T17:00:00Z",
    "venue": "Convention Center",
    "capacity": 500
}
```
- **Response**: Returns created event object with status 201

#### Get Event Details
- **GET** `/events/{id}/`
- **Description**: Retrieve details of a specific event
- **Response**: Returns event object

#### Update Event
- **PUT/PATCH** `/events/{id}/`
- **Description**: Update event details
- **Request Body**: Same as Create Event
- **Response**: Returns updated event object

#### Delete Event
- **DELETE** `/events/{id}/`
- **Description**: Delete an event
- **Response**: Status 204 No Content

### Track Management

#### List Tracks
- **GET** `/events/{event_id}/tracks/`
- **Description**: Get all tracks for an event
- **Response**:
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Technical Track",
            "description": "Technical sessions and workshops",
            "event": 1
        }
    ]
}
```

#### Create Track
- **POST** `/events/{event_id}/tracks/`
- **Request Body**:
```json
{
    "name": "Technical Track",
    "description": "Technical sessions and workshops"
}
```

### Session Management

#### List Sessions
- **GET** `/events/{event_id}/tracks/{track_id}/sessions/`
- **Description**: Get all sessions in a track
- **Response**:
```json
{
    "count": 3,
    "results": [
        {
            "id": 1,
            "title": "Introduction to AI",
            "description": "Overview of AI concepts",
            "speaker": {
                "id": 2,
                "name": "John Doe"
            },
            "start_time": "2024-06-01T10:00:00Z",
            "end_time": "2024-06-01T11:30:00Z",
            "capacity": 100
        }
    ]
}
```

#### Create Session
- **POST** `/events/{event_id}/tracks/{track_id}/sessions/`
- **Request Body**:
```json
{
    "title": "Introduction to AI",
    "description": "Overview of AI concepts",
    "speaker_id": 2,
    "start_time": "2024-06-01T10:00:00Z",
    "end_time": "2024-06-01T11:30:00Z",
    "capacity": 100
}
```

### Registration Management

#### Register for Event
- **POST** `/events/{id}/register/`
- **Description**: Register current user for an event
- **Response**:
```json
{
    "id": 1,
    "event": 1,
    "attendee": {
        "id": 3,
        "username": "attendee_user"
    },
    "status": "pending",
    "registration_date": "2024-01-15T14:30:00Z"
}
```

#### Approve Registration
- **POST** `/registrations/{id}/approve/`
- **Description**: Approve a pending registration (organizers only)
- **Response**: Returns updated registration object

#### Cancel Registration
- **POST** `/registrations/{id}/cancel/`
- **Description**: Cancel an event registration
- **Response**: Returns updated registration object

#### Register for Session
- **POST** `/events/{event_id}/tracks/{track_id}/sessions/{session_id}/register/`
- **Description**: Register for a specific session
- **Response**:
```json
{
    "id": 1,
    "session": 1,
    "attendee": {
        "id": 3,
        "username": "attendee_user"
    },
    "registration_date": "2024-01-15T14:35:00Z"
}
```

#### Cancel Session Registration
- **POST** `/session-registrations/{id}/cancel/`
- **Description**: Cancel a session registration
- **Response**: Returns updated session registration object

## Error Handling

The API uses standard HTTP response codes:

- 200: Success
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

Error responses follow this format:
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": {}
    }
}
```

## Rate Limiting

API requests are limited to:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

Rate limit information is included in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1516131012
```

## Best Practices

1. Always include proper authentication headers
2. Use pagination parameters for list endpoints
3. Handle rate limiting by checking response headers
4. Implement proper error handling for all possible response codes
5. Keep track of registration and session capacities

## Testing

A Postman collection is available in the `tests` directory for testing all API endpoints:
- `postman_collection.json`: Basic API tests
- `postman_collection_full.json`: Comprehensive test scenarios
- `postman_environment.json`: Environment variables

## Support

For API support or to report issues, please create an issue in the project repository.