# ASCAI Platform - Production Deployment Plan

**Version:** 1.0  
**Date:** 2025-01-27  
**Status:** Ready for Implementation

---

## Executive Summary

This document provides a comprehensive, step-by-step plan for deploying the ASCAI Django SaaS Platform to production. The plan covers infrastructure setup, security hardening, performance optimization, monitoring, and operational procedures.

**Estimated Deployment Timeline:** 2-3 weeks  
**Target Environment:** Linux server (Ubuntu 20.04/22.04 LTS recommended)  
**Application Stack:** Django 5.1.2 + PostgreSQL + Redis + Daphne/ASGI + Nginx

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Security Hardening](#security-hardening)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring & Logging](#monitoring--logging)
6. [Deployment Process](#deployment-process)
7. [Post-Deployment](#post-deployment)
8. [Backup & Disaster Recovery](#backup--disaster-recovery)
9. [Maintenance & Updates](#maintenance--updates)
10. [Troubleshooting Guide](#troubleshooting-guide)

---

## 1. Pre-Deployment Checklist

### 1.1 Code Readiness

- [x] All code committed to Git
- [x] Application state analysis completed
- [x] Production readiness analysis reviewed
- [ ] All critical bugs fixed
- [ ] Test suite passes (minimum 80% coverage)
- [ ] Security audit completed
- [ ] Performance testing completed
- [ ] Documentation updated

### 1.2 Environment Variables

Required production environment variables (must be set before deployment):

```bash
# Django Core
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
DJANGO_ENVIRONMENT=production
ALLOWED_HOSTS=ascai.it,www.ascai.it,api.ascai.it

# Database
DB_NAME=ascai_prod
DB_USER=ascai_user
DB_PASSWORD=<strong-password>
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=require

# Email (Production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@ascai.it

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# AWS S3 (File Storage)
AWS_ACCESS_KEY_ID=<aws-access-key>
AWS_SECRET_ACCESS_KEY=<aws-secret-key>
AWS_STORAGE_BUCKET_NAME=ascai-prod-media
AWS_S3_REGION_NAME=eu-central-1
AWS_S3_CUSTOM_DOMAIN=<cdn-domain>
AWS_DEFAULT_ACL=private
AWS_S3_OBJECT_PARAMETERS={'CacheControl': 'max-age=86400'}

# Stripe (Payment)
STRIPE_PUBLISHABLE_KEY=<stripe-publishable-key>
STRIPE_SECRET_KEY=<stripe-secret-key>
STRIPE_WEBHOOK_SECRET=<stripe-webhook-secret>

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Monitoring
SENTRY_DSN=<sentry-dsn>
SENTRY_ENVIRONMENT=production
```

### 1.3 Required Services

- [ ] Domain name configured (DNS)
- [ ] SSL certificate (Let's Encrypt)
- [ ] PostgreSQL database server
- [ ] Redis server
- [ ] AWS S3 bucket (for media files)
- [ ] Email service (SendGrid/Mailgun)
- [ ] Payment gateway (Stripe)
- [ ] Monitoring service (Sentry)
- [ ] Backup storage (S3/Backblaze)

---

## 2. Infrastructure Setup

### 2.1 Server Requirements

**Minimum Recommended Specifications:**
- **CPU:** 2 cores
- **RAM:** 4GB (8GB preferred)
- **Storage:** 50GB SSD (with backup space)
- **OS:** Ubuntu 22.04 LTS
- **Network:** Static IP address

**Additional Requirements:**
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Nginx
- Certbot (for SSL)

### 2.2 Server Initial Setup

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install essential packages
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

# 3. Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# 4. Create application user
sudo adduser --disabled-password --gecos "" ascai
sudo usermod -aG sudo ascai
sudo -u ascai mkdir -p /home/ascai/app
```

### 2.3 Database Setup

```bash
# 1. Switch to postgres user
sudo -u postgres psql

# 2. Create database and user
CREATE DATABASE ascai_prod ENCODING 'UTF8';
CREATE USER ascai_user WITH PASSWORD 'strong-password-here';
ALTER ROLE ascai_user SET client_encoding TO 'utf8';
ALTER ROLE ascai_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ascai_user SET timezone TO 'Europe/Rome';
GRANT ALL PRIVILEGES ON DATABASE ascai_prod TO ascai_user;

# 3. Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf

# Edit these settings:
# max_connections = 100
# shared_buffers = 256MB
# effective_cache_size = 1GB
# maintenance_work_mem = 64MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB
# default_statistics_target = 100
# random_page_cost = 1.1
# effective_io_concurrency = 200
# work_mem = 4MB
# min_wal_size = 1GB
# max_wal_size = 4GB

# 4. Configure PostgreSQL authentication
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add:
# host    ascai_prod    ascai_user    127.0.0.1/32    md5

# 5. Restart PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

### 2.4 Redis Setup

```bash
# 1. Configure Redis
sudo nano /etc/redis/redis.conf

# Edit these settings:
# maxmemory 512mb
# maxmemory-policy allkeys-lru
# requirepass your-redis-password-here
# bind 127.0.0.1

# 2. Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# 3. Test Redis connection
redis-cli -a your-redis-password-here ping
```

### 2.5 Application Setup

```bash
# 1. Switch to application user
sudo su - ascai

# 2. Clone repository
cd /home/ascai/app
git clone https://github.com/kouekamluc/ASCAI.git .
git checkout main

# 3. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install production dependencies
pip install gunicorn

# 6. Create .env file from template
cp env.example .env
nano .env  # Edit with production values

# 7. Create required directories
mkdir -p staticfiles media logs

# 8. Run migrations
python manage.py migrate

# 9. Collect static files
python manage.py collectstatic --noinput

# 10. Create superuser
python manage.py createsuperuser

# 11. Compile translations
python manage.py compilemessages
```

### 2.6 Gunicorn Configuration

Create `/home/ascai/app/gunicorn_config.py`:

```python
# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/home/ascai/app/logs/gunicorn_access.log"
errorlog = "/home/ascai/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ascai_gunicorn"

# Server mechanics
daemon = False
pidfile = "/home/ascai/app/gunicorn.pid"
umask = 0
user = "ascai"
group = "ascai"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### 2.7 Daphne Configuration (for WebSocket support)

Since the app uses Django Channels, we need Daphne for WebSocket support.

Create `/home/ascai/app/daphne_config.py`:

```python
# Daphne configuration for WebSocket support
bind = "127.0.0.1:8001"
endpoint = "tcp:port=8001:interface=127.0.0.1"
```

### 2.8 Supervisor Configuration

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

### 2.9 Nginx Configuration

Create `/etc/nginx/sites-available/ascai`:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name ascai.it www.ascai.it;

    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ascai.it www.ascai.it;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/ascai.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ascai.it/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;

    # Client body size (for file uploads)
    client_max_body_size 50M;

    # Static files
    location /static/ {
        alias /home/ascai/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files (from S3 CDN in production)
    location /media/ {
        alias /home/ascai/app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Gunicorn (HTTP requests)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket proxy to Daphne
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket timeouts
        proxy_read_timeout 86400;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ascai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 2.10 SSL Certificate Setup

```bash
# Install SSL certificate with Let's Encrypt
sudo certbot --nginx -d ascai.it -d www.ascai.it

# Test auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is configured automatically with certbot
```

---

## 3. Security Hardening

### 3.1 Django Security Settings

The application already includes production security settings in `config/settings.py`. Verify these are set correctly:

```python
# Already configured in settings.py:
- SECURE_SSL_REDIRECT = True
- SESSION_COOKIE_SECURE = True
- CSRF_COOKIE_SECURE = True
- SECURE_HSTS_SECONDS = 31536000
- SECURE_HSTS_INCLUDE_SUBDOMAINS = True
- SECURE_HSTS_PRELOAD = True
- SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
- X_FRAME_OPTIONS = "DENY"
- SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

### 3.2 Additional Security Measures

**1. Rate Limiting** (already in requirements, needs implementation)

Add to critical views:
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # existing code
```

**2. Fail2ban Configuration**

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
```

**3. Security.txt File**

Create `/home/ascai/app/staticfiles/.well-known/security.txt`:

```
Contact: security@ascai.it
Expires: 2025-12-31T23:59:59.000Z
Preferred-Languages: en, it, fr
Canonical: https://ascai.it/.well-known/security.txt
```

**4. Database Security**

```bash
# PostgreSQL: Remove default postgres user password
sudo -u postgres psql -c "ALTER USER postgres PASSWORD NULL;"

# Only allow local connections
# Already configured in pg_hba.conf
```

### 3.3 File Upload Security

**Add file validation in models/views:**

```python
import magic
from django.core.exceptions import ValidationError

ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png',
    'image/gif',
]

def validate_file_type(file):
    mime = magic.Magic(mime=True)
    file_mime = mime.from_buffer(file.read(1024))
    file.seek(0)
    
    if file_mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(f'File type {file_mime} not allowed')
```

---

## 4. Performance Optimization

### 4.1 Database Optimization

**1. Add Database Indexes**

Create migration:
```python
# apps/members/migrations/XXXX_add_indexes.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('members', 'previous_migration'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_member_user_email ON accounts_user(email);",
            reverse_sql="DROP INDEX IF EXISTS idx_member_user_email;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_member_status ON members_member(status);",
            reverse_sql="DROP INDEX IF EXISTS idx_member_status;"
        ),
        # Add more indexes as needed
    ]
```

**2. Query Optimization**

Ensure views use `select_related` and `prefetch_related`:
```python
# Example
members = Member.objects.select_related('user').prefetch_related('badges').all()
```

**3. Database Connection Pooling**

Already configured in `settings.py`:
```python
CONN_MAX_AGE = 600  # 10 minutes
```

### 4.2 Caching Strategy

**1. Page-level Caching**

Add to views:
```python
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

@cache_page(60 * 15)  # 15 minutes
@vary_on_headers('Cookie')
def news_list(request):
    # existing code
```

**2. Template Fragment Caching**

```django
{% load cache %}
{% cache 600 sidebar request.user.id %}
    <!-- Sidebar content -->
{% endcache %}
```

**3. Cache Invalidation**

```python
from django.core.cache import cache

# Invalidate cache after model update
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    cache.delete('member_list_cache')
```

### 4.3 Static Files Optimization

**1. Enable Compression**

Already configured in Nginx (gzip).

**2. Use CDN for Static Files**

Update `settings.py`:
```python
if IS_PRODUCTION:
    STATIC_URL = 'https://cdn.ascai.it/static/'
    # Configure AWS CloudFront or similar CDN
```

### 4.4 Celery Task Optimization

**1. Configure Celery for Production**

Create `config/celery.py` (if not exists):
```python
from celery import Celery
from django.conf import settings

app = Celery('ascai')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Production optimizations
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Rome',
    enable_utc=True,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)
```

---

## 5. Monitoring & Logging

### 5.1 Error Tracking (Sentry)

**1. Install Sentry SDK**

```bash
pip install sentry-sdk
```

**2. Configure in settings.py**

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

if IS_PRODUCTION:
    sentry_sdk.init(
        dsn=get_env_config("SENTRY_DSN"),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=True,
        environment="production",
    )
```

### 5.2 Logging Configuration

Already configured in `settings.py`. Verify log rotation:

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/ascai

# Add:
/home/ascai/app/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ascai ascai
    sharedscripts
}
```

### 5.3 Uptime Monitoring

Set up external monitoring:
- **UptimeRobot** (free tier: 50 monitors)
- **Pingdom** (paid)
- **StatusCake** (free tier available)

Monitor:
- Main site (https://ascai.it)
- API endpoints
- WebSocket connections
- Database connectivity

### 5.4 Application Monitoring

**1. Health Check Endpoint**

Create `apps/dashboard/views.py`:

```python
from django.http import JsonResponse
from django.db import connection
import redis

def health_check(request):
    status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Redis check
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        status['checks']['redis'] = 'ok'
    except Exception as e:
        status['checks']['redis'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status, status=200 if status['status'] == 'healthy' else 503)
```

**2. Metrics Collection**

Consider integrating:
- **Prometheus** + **Grafana** (self-hosted)
- **Datadog** (paid, comprehensive)
- **New Relic** (paid)

---

## 6. Deployment Process

### 6.1 Initial Deployment

```bash
# 1. On server, as ascai user
sudo su - ascai
cd /home/ascai/app

# 2. Pull latest code
git pull origin main

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install/update dependencies
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Compile translations
python manage.py compilemessages

# 8. Restart services
sudo supervisorctl restart ascai_gunicorn
sudo supervisorctl restart ascai_daphne
sudo supervisorctl restart ascai_celery
sudo supervisorctl restart ascai_celery_beat

# 9. Reload Nginx
sudo nginx -t && sudo systemctl reload nginx
```

### 6.2 Zero-Downtime Deployment Script

Create `/home/ascai/app/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "Starting deployment..."

# Activate virtual environment
source /home/ascai/app/venv/bin/activate

# Pull latest code
cd /home/ascai/app
git fetch origin
git checkout main
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Compile translations
python manage.py compilemessages

# Restart services gracefully
sudo supervisorctl restart ascai_gunicorn:ascai_gunicorn_00
sleep 2
sudo supervisorctl restart ascai_gunicorn:ascai_gunicorn_01
sleep 2
sudo supervisorctl restart ascai_daphne
sudo supervisorctl restart ascai_celery
sudo supervisorctl restart ascai_celery_beat

# Reload Nginx
sudo nginx -t && sudo systemctl reload nginx

echo "Deployment complete!"

# Health check
sleep 5
curl -f http://localhost:8000/health/ || echo "Health check failed!"
```

```bash
chmod +x /home/ascai/app/deploy.sh
```

### 6.3 CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /home/ascai/app
            ./deploy.sh
```

---

## 7. Post-Deployment

### 7.1 Verification Checklist

- [ ] Site loads at https://ascai.it
- [ ] SSL certificate valid
- [ ] User registration works
- [ ] Email sending works
- [ ] File uploads work
- [ ] WebSocket connections work
- [ ] Static files load correctly
- [ ] Admin panel accessible
- [ ] Database queries perform well
- [ ] Logs are being written
- [ ] Monitoring alerts configured

### 7.2 Performance Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test homepage
ab -n 1000 -c 10 https://ascai.it/

# Test API endpoints
ab -n 500 -c 5 https://ascai.it/api/endpoint/
```

### 7.3 Security Testing

- [ ] Run `python manage.py check --deploy`
- [ ] Test SSL configuration: https://www.ssllabs.com/ssltest/
- [ ] Verify security headers: https://securityheaders.com/
- [ ] Test rate limiting
- [ ] Verify CSRF protection
- [ ] Test file upload restrictions

---

## 8. Backup & Disaster Recovery

### 8.1 Database Backups

**1. Automated Backup Script**

Create `/home/ascai/app/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/ascai/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="ascai_db_${DATE}.sql.gz"

mkdir -p $BACKUP_DIR

# Backup database
PGPASSWORD=$DB_PASSWORD pg_dump -h localhost -U ascai_user -d ascai_prod | gzip > "$BACKUP_DIR/$FILENAME"

# Keep only last 30 days
find $BACKUP_DIR -name "ascai_db_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp "$BACKUP_DIR/$FILENAME" s3://ascai-backups/database/
```

**2. Cron Job**

```bash
sudo crontab -e

# Add (daily at 2 AM):
0 2 * * * /home/ascai/app/backup_db.sh
```

### 8.2 Media Files Backup

```bash
# Backup to S3
aws s3 sync /home/ascai/app/media/ s3://ascai-backups/media/ --delete
```

### 8.3 Backup Restoration

**Database:**
```bash
gunzip < backup_file.sql.gz | psql -h localhost -U ascai_user -d ascai_prod
```

**Media Files:**
```bash
aws s3 sync s3://ascai-backups/media/ /home/ascai/app/media/
```

### 8.4 Disaster Recovery Plan

1. **Document recovery procedures**
2. **Test backups monthly**
3. **Keep offsite backups (S3)**
4. **Document contact information**
5. **Define RTO (Recovery Time Objective): 4 hours**
6. **Define RPO (Recovery Point Objective): 24 hours**

---

## 9. Maintenance & Updates

### 9.1 Regular Maintenance Tasks

**Weekly:**
- [ ] Review error logs
- [ ] Check disk space
- [ ] Review security alerts
- [ ] Monitor performance metrics

**Monthly:**
- [ ] Update system packages
- [ ] Update Python dependencies
- [ ] Review and rotate logs
- [ ] Test backup restoration
- [ ] Review monitoring dashboards

**Quarterly:**
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Dependency security scan
- [ ] SSL certificate renewal check

### 9.2 Update Procedure

```bash
# 1. Create backup
./backup_db.sh

# 2. Test on staging (if available)

# 3. Update code
git pull origin main

# 4. Update dependencies
pip install -r requirements.txt --upgrade

# 5. Run migrations
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Restart services
sudo supervisorctl restart all

# 8. Verify deployment
curl http://localhost:8000/health/
```

### 9.3 Dependency Updates

```bash
# Check for outdated packages
pip list --outdated

# Update requirements.txt
pip freeze > requirements.txt

# Test updates locally before production
```

---

## 10. Troubleshooting Guide

### 10.1 Common Issues

**Issue: 502 Bad Gateway**
```bash
# Check Gunicorn status
sudo supervisorctl status ascai_gunicorn

# Check logs
tail -f /home/ascai/app/logs/gunicorn_error.log

# Restart service
sudo supervisorctl restart ascai_gunicorn
```

**Issue: Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U ascai_user -d ascai_prod

# Check connection pool
ps aux | grep postgres
```

**Issue: Redis Connection Error**
```bash
# Check Redis status
sudo systemctl status redis-server

# Test connection
redis-cli -a your-password ping

# Check memory
redis-cli -a your-password INFO memory
```

**Issue: Static Files Not Loading**
```bash
# Re-collect static files
python manage.py collectstatic --noinput

# Check permissions
ls -la /home/ascai/app/staticfiles/

# Check Nginx configuration
sudo nginx -t
```

**Issue: WebSocket Connection Fails**
```bash
# Check Daphne status
sudo supervisorctl status ascai_daphne

# Check logs
tail -f /home/ascai/app/logs/daphne.log

# Verify Nginx WebSocket configuration
grep -A 10 "location /ws/" /etc/nginx/sites-available/ascai
```

### 10.2 Performance Issues

**Slow Database Queries:**
```bash
# Enable query logging in PostgreSQL
# Analyze slow queries
# Add indexes
# Use select_related/prefetch_related
```

**High Memory Usage:**
```bash
# Monitor memory
free -h
htop

# Adjust Gunicorn workers
# Reduce Redis maxmemory
# Optimize database queries
```

### 10.3 Emergency Contacts

- **System Administrator:** [contact info]
- **Database Administrator:** [contact info]
- **Hosting Provider Support:** [contact info]
- **Domain Registrar:** [contact info]

---

## 11. Additional Resources

### 11.1 Useful Commands

```bash
# View application logs
tail -f /home/ascai/app/logs/django.log
tail -f /home/ascai/app/logs/gunicorn_error.log
tail -f /home/ascai/app/logs/celery.log

# Check service status
sudo supervisorctl status

# Restart all services
sudo supervisorctl restart all

# Reload Nginx
sudo nginx -t && sudo systemctl reload nginx

# Check disk space
df -h

# Check memory usage
free -h

# Check active connections
netstat -tulpn | grep :8000
```

### 11.2 Documentation Links

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

---

## 12. Timeline & Milestones

### Week 1: Infrastructure Setup
- [ ] Server provisioning
- [ ] Database setup
- [ ] Redis setup
- [ ] Application deployment
- [ ] SSL certificate installation

### Week 2: Security & Optimization
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Monitoring setup
- [ ] Backup configuration

### Week 3: Testing & Launch
- [ ] Load testing
- [ ] Security testing
- [ ] User acceptance testing
- [ ] Documentation completion
- [ ] Production launch

---

## Conclusion

This production deployment plan provides a comprehensive guide for deploying the ASCAI platform to production. Follow each section sequentially, and verify all checkboxes before proceeding to the next phase.

**Key Success Factors:**
1. ✅ Thorough testing before launch
2. ✅ Proper security configuration
3. ✅ Monitoring and alerting in place
4. ✅ Backup and recovery procedures tested
5. ✅ Documentation complete and accessible

**Questions or Issues?**
Refer to the troubleshooting guide or contact the development team.

---

**Last Updated:** 2025-01-27  
**Document Version:** 1.0  
**Next Review:** 2025-04-27

