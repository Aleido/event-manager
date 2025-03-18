# Event Management System

A Django-based REST API for managing events, tracks, sessions, and registrations.

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TestMIndo1
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Run database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. Create a superuser account:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. Access the API:
   - API Root: http://localhost:8000/api/
   - Admin Interface: http://localhost:8000/admin/
   - API Documentation: http://localhost:8000/api/schema/swagger-ui/

## Development Setup

### Local Development without Docker

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env` file:
   ```env
   DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
   POSTGRES_DB=eventmanagement
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## API Features

- User Authentication (JWT)
- Event Management
- Track Management
- Session Management
- Registration System
- Permission-based Access Control

## Testing

Run the test suite:
```bash
docker-compose exec web python manage.py test
```

Detailed API documentation and test cases can be found in the `events/tests/` directory.

## Project Structure

```
├── eventmanagement/  # Project settings and configuration
├── events/           # Event management app
├── users/            # User management app
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker configuration
└── docker-compose.yml # Docker Compose configuration
```
