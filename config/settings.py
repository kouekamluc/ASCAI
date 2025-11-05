"""
Django settings for ASCAI platform.
"""

from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
DJANGO_ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "development").lower()
IS_PRODUCTION = DJANGO_ENVIRONMENT == "production"
IS_DEVELOPMENT = not IS_PRODUCTION

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ValueError("SECRET_KEY environment variable must be set in production!")
    # Only allow default in development
    SECRET_KEY = "django-insecure-630ws57esm5mxwje2zhcmj_0%)w7^1tzdbnik_z+%z=@=x%%6#"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "False" if IS_PRODUCTION else "True").lower() == "true"

# Parse ALLOWED_HOSTS from environment or use defaults
ALLOWED_HOSTS_ENV = os.environ.get("ALLOWED_HOSTS", "")
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(",")]
else:
    if IS_PRODUCTION:
        raise ValueError("ALLOWED_HOSTS environment variable must be set in production!")
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Application definition
INSTALLED_APPS = [
    "daphne",  # Must be first for ASGI support
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    
    # Third-party apps
    "channels",
    "ckeditor",
    "ckeditor_uploader",
    "django_htmx",
    
    # Local apps
    "apps.accounts",
    "apps.members",
    "apps.events",
    "apps.news",
    "apps.documents",
    "apps.jobs",
    "apps.forums",
    "apps.payments",
    "apps.dashboard",
    "apps.messaging",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database - PostgreSQL Configuration
# PostgreSQL is the primary database for this project
# Make sure PostgreSQL is running and the database exists
# Create database with: CREATE DATABASE "ascai" ENCODING 'UTF8';
# 
# IMPORTANT: Set DB_PASSWORD in your .env file or environment variables
# If PostgreSQL requires authentication, you must provide the password.
# 
# To set up environment variables:
# 1. Copy env.example to .env: cp env.example .env
# 2. Edit .env and set DB_PASSWORD=your_postgres_password
# 3. Also set DB_NAME, DB_USER, DB_HOST, DB_PORT if different from defaults

# Try to load environment variables from .env file if python-decouple is available
try:
    from decouple import config
    USE_DECOUPLE = True
except ImportError:
    USE_DECOUPLE = False

def get_db_config(key, default=None, cast=None):
    """Get database configuration with fallback to environment variables."""
    if USE_DECOUPLE:
        try:
            return config(key, default=default, cast=cast)
        except Exception:
            return default
    value = os.environ.get(key)
    if value is None:
        return default
    if cast:
        return cast(value)
    return value

# Channels configuration (Redis)
# In production, use environment variable for Redis URL
REDIS_URL = get_db_config("REDIS_URL", "redis://127.0.0.1:6379/0")
if IS_PRODUCTION and ("localhost" in REDIS_URL or "127.0.0.1" in REDIS_URL):
    import warnings
    warnings.warn(
        "Redis is configured to use localhost. In production, use a dedicated Redis instance "
        "with proper authentication. Set REDIS_URL environment variable."
    )

# Parse Redis URL for channels_redis
# Format: redis://host:port/db or redis://host:port
try:
    redis_url_clean = REDIS_URL.replace("redis://", "").replace("rediss://", "")
    if "/" in redis_url_clean:
        redis_host_port, redis_db = redis_url_clean.split("/", 1)
    else:
        redis_host_port = redis_url_clean
        redis_db = "0"
    
    if ":" in redis_host_port:
        redis_host, redis_port = redis_host_port.split(":", 1)
        redis_port = int(redis_port)
    else:
        redis_host = redis_host_port
        redis_port = 6379
    
    REDIS_HOST = redis_host
    REDIS_PORT = redis_port
except Exception:
    # Fallback to defaults if parsing fails
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Get database configuration
# Default values match your PostgreSQL setup
DB_NAME = get_db_config("DB_NAME", "ASCAI")
DB_USER = get_db_config("DB_USER", "postgres")
DB_PASSWORD = get_db_config("DB_PASSWORD", "kouekam")
DB_HOST = get_db_config("DB_HOST", "localhost")
DB_PORT = get_db_config("DB_PORT", "5432", cast=int)

# Require database password in production
if IS_PRODUCTION and not DB_PASSWORD:
    raise ValueError(
        "DB_PASSWORD environment variable must be set in production! "
        "Database credentials cannot be hardcoded."
    )

# Determine SSL mode based on environment
# Production: require SSL for secure connections
# Development: prefer SSL but allow non-SSL
if IS_PRODUCTION:
    default_sslmode = "require"
    # In production, prefer verify-full for maximum security (requires CA certificate)
    # Fall back to require if verify-full is not configured
    sslmode = get_db_config("DB_SSLMODE", "require")
    if sslmode not in ["require", "verify-ca", "verify-full"]:
        sslmode = "require"
else:
    default_sslmode = "prefer"
    sslmode = get_db_config("DB_SSLMODE", "prefer")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {
            "connect_timeout": 30 if IS_PRODUCTION else 10,  # Longer timeout for production
            "options": "-c timezone=Europe/Rome -c client_encoding=UTF8",
            # PostgreSQL-specific optimizations
            "sslmode": sslmode,
        },
        # Connection pooling: optimized for production
        "CONN_MAX_AGE": 600 if IS_PRODUCTION else 0,  # Keep connections alive in production
        "ATOMIC_REQUESTS": False,  # Set to False for better performance (use transactions explicitly)
        "AUTOCOMMIT": True,
        # PostgreSQL connection test settings
        "TEST": {
            "NAME": get_db_config("TEST_DB_NAME", "test_ASCAI"),
            "CHARSET": "UTF8",
        },
    }
}

# Database connection validation
# In production, validate connection silently (no prints)
# In development, provide helpful error messages
if IS_DEVELOPMENT and DEBUG:
    try:
        from django.db import connections
        db_conn = connections["default"]
        db_conn.ensure_connection()
        # Use ASCII-safe characters for Windows compatibility
        print("[OK] PostgreSQL connection successful!")
        print(f"     Database: {DB_NAME} | User: {DB_USER} | Host: {DB_HOST}:{DB_PORT}")
    except Exception as e:
        error_msg = str(e)
        print("[WARNING] PostgreSQL connection failed!")
        print(f"     Error: {error_msg}")
        print(f"     Configuration: Database={DB_NAME}, User={DB_USER}, Host={DB_HOST}:{DB_PORT}")
        if "password" in error_msg.lower() or "authentication" in error_msg.lower():
            print("\n     Solution: Set DB_PASSWORD in your .env file or environment variables.")
            print("     Create .env file from env.example and set:")
            print("     DB_PASSWORD=your_postgres_password")
        elif "does not exist" in error_msg.lower():
            print("\n     Solution: Create the database in PostgreSQL:")
            print(f'     CREATE DATABASE "{DB_NAME}" ENCODING \'UTF8\';')
        elif "could not connect" in error_msg.lower():
            print(f"\n     Solution: Make sure PostgreSQL is running on {DB_HOST}:{DB_PORT}")
        print("\n     For help, see: env.example file or README.md")
elif IS_PRODUCTION:
    # In production, validate connection but don't print to console
    try:
        from django.db import connections
        db_conn = connections["default"]
        db_conn.ensure_connection()
    except Exception as e:
        # Log error but don't crash during settings load
        # The actual error will surface when the app tries to use the database
        import logging
        logger = logging.getLogger(__name__)
        logger.critical(f"Production database connection failed: {str(e)}")

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("it", _("Italian")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "Europe/Rome"

USE_I18N = True
USE_L10N = True  # Enable locale-aware formatting for dates, numbers, and times

USE_TZ = True

# Locale-aware formatting
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = "."  # Default, will be overridden by locale
THOUSAND_SEPARATOR = ","  # Default, will be overridden by locale
NUMBER_GROUPING = 3

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Site ID for django.contrib.sites
SITE_ID = 1

# Email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@ascai.it")

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Production security settings
if IS_PRODUCTION:
    # HTTPS settings
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() == "true"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    
    # Additional security headers
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    
    # Prevent clickjacking
    X_FRAME_OPTIONS = "DENY"
else:
    # Development settings - less strict
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# CKEditor settings
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline"],
            ["NumberedList", "BulletedList", "-", "Outdent", "Indent", "-", "JustifyLeft", "JustifyCenter", "JustifyRight", "JustifyBlock"],
            ["Link", "Unlink"],
            ["RemoveFormat", "Source"],
        ],
        "height": 300,
        "width": "100%",
        "disableNativeSpellChecker": False,
    },
}

