"""
Gunicorn configuration file for ASCAI platform.
"""
import multiprocessing
import os

# Server socket
bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8000")
backlog = 2048

# Worker processes
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "logs/gunicorn_access.log")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "logs/gunicorn_error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ascai_gunicorn"

# Server mechanics
daemon = False
pidfile = os.getenv("GUNICORN_PIDFILE", "gunicorn.pid")
umask = 0
user = os.getenv("GUNICORN_USER", None)
group = os.getenv("GUNICORN_GROUP", None)
tmp_upload_dir = None

# SSL (if needed - usually handled by reverse proxy)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Maximum requests per worker before restart (helps prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

