# ASCAI Platform - Production Deployment Quick Start Guide

This guide provides step-by-step instructions for deploying the ASCAI platform to production.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start Options](#quick-start-options)
3. [Option 1: Traditional Server Deployment](#option-1-traditional-server-deployment)
4. [Option 2: Docker Deployment](#option-2-docker-deployment)
5. [Post-Deployment](#post-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- ✅ A server with Ubuntu 20.04/22.04 LTS (or similar Linux distribution)
- ✅ Domain name configured with DNS pointing to your server
- ✅ SSH access to your server
- ✅ PostgreSQL database (or use Docker)
- ✅ Redis server (or use Docker)
- ✅ SSL certificate (Let's Encrypt recommended)

---

## Quick Start Options

You have two main deployment options:

1. **Traditional Server Deployment** - Deploy directly on a Linux server
2. **Docker Deployment** - Use Docker Compose for containerized deployment

Choose the option that best fits your infrastructure.

---

## Option 1: Traditional Server Deployment

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    certbot python3-certbot-nginx \
    git \
    curl \
    supervisor \
    ufw \
    fail2ban

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Step 2: Create Application User

```bash
# Create application user
sudo adduser --disabled-password --gecos "" ascai
sudo usermod -aG sudo ascai
sudo -u ascai mkdir -p /home/ascai/app
```

### Step 3: Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE ascai_prod ENCODING 'UTF8';
CREATE USER ascai_user WITH PASSWORD 'your-strong-password-here';
ALTER ROLE ascai_user SET client_encoding TO 'utf8';
ALTER ROLE ascai_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ascai_user SET timezone TO 'Europe/Rome';
GRANT ALL PRIVILEGES ON DATABASE ascai_prod TO ascai_user;
\q
```

### Step 4: Redis Setup

```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Edit these settings:
# maxmemory 512mb
# maxmemory-policy allkeys-lru
# requirepass your-redis-password-here
# bind 127.0.0.1

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### Step 5: Deploy Application

```bash
# Switch to application user
sudo su - ascai

# Clone repository
cd /home/ascai/app
git clone <your-repository-url> .
git checkout main

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp env.example .env
nano .env  # Edit with production values (see below)
```

### Step 6: Configure Environment Variables

Edit `.env` file with production values:

```bash
# Django Settings
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
DJANGO_ENVIRONMENT=production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=ascai_prod
DB_USER=ascai_user
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=require

# Redis
REDIS_URL=redis://:your-redis-password@localhost:6379/0
CELERY_BROKER_URL=redis://:your-redis-password@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:your-redis-password@localhost:6379/1

# Email (Production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@ascai.it

# AWS S3 (Optional - for file storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_STORAGE_BUCKET_NAME=ascai-prod-media
AWS_S3_REGION_NAME=eu-central-1
```

**Generate Secret Key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 7: Initialize Application

```bash
# Create required directories
mkdir -p staticfiles media logs

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Compile translations
python manage.py compilemessages

# Create superuser
python manage.py createsuperuser
```

### Step 8: Configure Supervisor

Create `/etc/supervisor/conf.d/ascai.conf`:

```ini
[program:ascai_gunicorn]
directory=/home/ascai/app
command=/home/ascai/app/venv/bin/gunicorn config.wsgi:application --config /home/ascai/app/gunicorn_config.py
user=ascai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ascai/app/logs/gunicorn.log
environment=DJANGO_ENVIRONMENT="production"

[program:ascai_daphne]
directory=/home/ascai/app
command=/home/ascai/app/venv/bin/daphne -b 127.0.0.1 -p 8001 config.asgi:application
user=ascai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ascai/app/logs/daphne.log
environment=DJANGO_ENVIRONMENT="production"

[program:ascai_celery]
directory=/home/ascai/app
command=/home/ascai/app/venv/bin/celery -A config worker --loglevel=info --concurrency=4
user=ascai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ascai/app/logs/celery.log
environment=DJANGO_ENVIRONMENT="production"

[program:ascai_celery_beat]
directory=/home/ascai/app
command=/home/ascai/app/venv/bin/celery -A config beat --loglevel=info
user=ascai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/ascai/app/logs/celery_beat.log
environment=DJANGO_ENVIRONMENT="production"
```

```bash
# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### Step 9: Configure Nginx

Create `/etc/nginx/sites-available/ascai` (see `PRODUCTION_DEPLOYMENT_PLAN.md` for full configuration):

```bash
sudo nano /etc/nginx/sites-available/ascai
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ascai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 10: SSL Certificate

```bash
# Install SSL certificate with Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 11: Make Deployment Script Executable

```bash
chmod +x /home/ascai/app/deploy.sh
```

---

## Option 2: Docker Deployment

### Step 1: Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### Step 2: Clone Repository

```bash
git clone <your-repository-url> ascai
cd ascai
```

### Step 3: Configure Environment

```bash
# Create .env file
cp env.example .env
nano .env  # Edit with production values
```

### Step 4: Build and Start Services

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Step 5: Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Compile translations
docker-compose exec web python manage.py compilemessages
```

### Step 6: SSL Certificate (Optional)

For production, configure SSL certificates in the `nginx/ssl` directory or use a reverse proxy like Traefik.

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health/

# Check service status
sudo supervisorctl status  # Traditional deployment
# OR
docker-compose ps  # Docker deployment
```

### 2. Test Application

- ✅ Visit your domain in a browser
- ✅ Test user registration
- ✅ Test login/logout
- ✅ Verify static files load
- ✅ Test WebSocket connections (if applicable)
- ✅ Check admin panel

### 3. Set Up Monitoring

- Configure uptime monitoring (UptimeRobot, Pingdom)
- Set up error tracking (Sentry)
- Configure log aggregation
- Set up backup automation

### 4. Configure Backups

```bash
# Create backup script
nano /home/ascai/app/backup_db.sh
chmod +x /home/ascai/app/backup_db.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/ascai/app/backup_db.sh
```

---

## Troubleshooting

### Issue: 502 Bad Gateway

```bash
# Check Gunicorn status
sudo supervisorctl status ascai_gunicorn

# Check logs
tail -f /home/ascai/app/logs/gunicorn_error.log

# Restart service
sudo supervisorctl restart ascai_gunicorn
```

### Issue: Database Connection Error

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U ascai_user -d ascai_prod

# Check .env file
cat /home/ascai/app/.env | grep DB_
```

### Issue: Static Files Not Loading

```bash
# Re-collect static files
python manage.py collectstatic --noinput

# Check permissions
ls -la /home/ascai/app/staticfiles/

# Check Nginx configuration
sudo nginx -t
```

### Issue: Redis Connection Error

```bash
# Check Redis status
sudo systemctl status redis-server

# Test connection
redis-cli -a your-password ping

# Check Redis URL in .env
cat /home/ascai/app/.env | grep REDIS
```

### View Logs

```bash
# Application logs
tail -f /home/ascai/app/logs/django.log

# Gunicorn logs
tail -f /home/ascai/app/logs/gunicorn_error.log

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Quick Reference Commands

### Traditional Deployment

```bash
# Deploy updates
cd /home/ascai/app && ./deploy.sh

# Restart services
sudo supervisorctl restart all

# View logs
tail -f /home/ascai/app/logs/django.log
```

### Docker Deployment

```bash
# Deploy updates
docker-compose pull
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Restart services
docker-compose restart

# Access shell
docker-compose exec web bash
```

---

## Next Steps

1. ✅ Review `PRODUCTION_DEPLOYMENT_PLAN.md` for detailed configuration
2. ✅ Review `PRODUCTION_READINESS_ANALYSIS.md` for security improvements
3. ✅ Set up monitoring and alerting
4. ✅ Configure automated backups
5. ✅ Set up CI/CD pipeline (optional)

---

## Support

For issues or questions:
- Check logs: `/home/ascai/app/logs/`
- Review documentation: `PRODUCTION_DEPLOYMENT_PLAN.md`
- Check Django system checks: `python manage.py check --deploy`

---

**Last Updated:** 2025-01-27  
**Version:** 1.0

