#!/bin/bash
# Deployment script for ASCAI platform
# This script handles zero-downtime deployment

set -e  # Exit on any error

echo "=========================================="
echo "ASCAI Platform - Production Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="${APP_DIR:-/home/ascai/app}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
LOG_DIR="${LOG_DIR:-$APP_DIR/logs}"

# Check if running as correct user (optional check)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Warning: Running as root. Consider running as application user.${NC}"
fi

# Activate virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    exit 1
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Navigate to app directory
cd "$APP_DIR" || exit 1

# Pull latest code
echo ""
echo "Pulling latest code from repository..."
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
git pull origin "$CURRENT_BRANCH"

# Install/update dependencies
echo ""
echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo ""
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Compile translations
echo ""
echo "Compiling translations..."
python manage.py compilemessages

# Run Django checks
echo ""
echo "Running Django system checks..."
python manage.py check --deploy

# Restart services (using supervisor)
echo ""
echo "Restarting application services..."

# Check if supervisor is available
if command -v supervisorctl &> /dev/null; then
    # Restart services one by one for zero-downtime
    echo "Restarting Gunicorn workers..."
    supervisorctl restart ascai_gunicorn || echo "Warning: Could not restart Gunicorn via supervisor"
    
    sleep 2
    
    echo "Restarting Daphne (WebSocket server)..."
    supervisorctl restart ascai_daphne || echo "Warning: Could not restart Daphne via supervisor"
    
    sleep 2
    
    echo "Restarting Celery worker..."
    supervisorctl restart ascai_celery || echo "Warning: Could not restart Celery via supervisor"
    
    sleep 2
    
    echo "Restarting Celery beat..."
    supervisorctl restart ascai_celery_beat || echo "Warning: Could not restart Celery beat via supervisor"
else
    echo -e "${YELLOW}Warning: supervisorctl not found. Services may need to be restarted manually.${NC}"
fi

# Reload Nginx (if available)
if command -v nginx &> /dev/null; then
    echo ""
    echo "Reloading Nginx..."
    sudo nginx -t && sudo systemctl reload nginx || echo -e "${YELLOW}Warning: Could not reload Nginx${NC}"
fi

# Health check
echo ""
echo "Performing health check..."
sleep 5

HEALTH_URL="http://localhost:8000/health/"
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ Health check passed (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${RED}✗ Health check failed (HTTP $HTTP_CODE)${NC}"
        echo "Check logs for more information:"
        echo "  - Application logs: $LOG_DIR/django.log"
        echo "  - Gunicorn logs: $LOG_DIR/gunicorn_error.log"
        exit 1
    fi
else
    echo -e "${YELLOW}Warning: curl not found. Skipping health check.${NC}"
fi

# Display service status
echo ""
echo "Service status:"
if command -v supervisorctl &> /dev/null; then
    supervisorctl status | grep ascai || echo "No ASCAI services found in supervisor"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment completed successfully!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Monitor application logs: tail -f $LOG_DIR/django.log"
echo "  2. Check service status: supervisorctl status"
echo "  3. Verify site is accessible"
echo ""

