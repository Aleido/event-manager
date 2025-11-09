#!/bin/sh

# Wait for PostgreSQL to be ready
echo "Waiting for postgres..."

while ! nc -z db 5432; do
  sleep 0.1
done

echo "PostgreSQL started"

# Apply database migrations
python manage.py migrate --noinput

# Create sample user if it doesn't exist
python manage.py create_sample_user

# {{ edit_1 }}
# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput
# {{ /edit_1 }}

# Create superuser if it doesn't exist (optional, but good for dev)
# You might want to make this conditional or remove it for production
# python manage.py createsuperuser --noinput || true

# Execute the main command (e.g., gunicorn)
exec "$@"