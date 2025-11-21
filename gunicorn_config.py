"""
Gunicorn configuration for ASCAI.

Ensures each worker closes inherited Django DB connections after forking to
avoid SSL errors ("decryption failed or bad record mac") when using pooled
connections with PostgreSQL.
"""

from django.db import connections


def post_fork(server, worker):
    """
    Called by Gunicorn in each worker process immediately after forking.

    Closing inherited connections forces Django to establish fresh ones per
    worker, preventing the SSL corruption that occurs when multiple workers
    share the same connection handle.
    """

    for conn in connections.all():
        conn.close()

    worker.log.info("Database connections closed after worker fork.")


# Log Gunicorn errors to stdout/stderr so Render can capture them
errorlog = "-"
accesslog = "-"
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

