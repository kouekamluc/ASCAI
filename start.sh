#!/bin/bash
# Production startup script for ASCAI platform
# This script starts all required services

set -e

echo "Starting ASCAI Platform services..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment
export DJANGO_ENVIRONMENT=production

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Compile translations
echo "Compiling translations..."
python manage.py compilemessages

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --config gunicorn_config.py \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 30 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info

