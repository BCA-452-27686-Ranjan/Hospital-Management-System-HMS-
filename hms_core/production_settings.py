"""
Production settings for HMS
"""
import os
from decouple import config
from .settings import *

# SECURITY SETTINGS
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Security middleware
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Database settings for production
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='hms_prod'),
        'USER': config('DB_USER', default='hms_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'charset': 'utf8',
        },
    }
}

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@hms.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='admin@hms.com')

# Static and media files for production
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'hms.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'appointments': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': config('CACHE_BACKEND', default='django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': config('CACHE_LOCATION', default='unique-snowflake'),
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
        'OPTIONS': {
            'MAX_ENTRIES': config('CACHE_MAX_ENTRIES', default=1000, cast=int),
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache.SessionBackend'
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=3600, cast=int)  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Performance settings
CONN_MAX_AGE = config('CONN_MAX_AGE', default=60, cast=int)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('API_PAGE_SIZE', default=20, cast=int),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

# CORS settings for API
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# Health check
HEALTH_CHECK = {
    'DISALLOWED_SERVICES': ['database'],
    'ALLOWED_HOSTS': ALLOWED_HOSTS,
}

# Monitoring and analytics
SENTRY_DSN = config('SENTRY_DSN', default='')
LOGOUT_REDIRECT_URL = config('LOGOUT_REDIRECT_URL', default='/')

# Backup settings
BACKUP_ENABLED = config('BACKUP_ENABLED', default=True, cast=bool)
BACKUP_SCHEDULE = config('BACKUP_SCHEDULE', default='0 2 * * *')  # Daily at 2 AM
BACKUP_RETENTION_DAYS = config('BACKUP_RETENTION_DAYS', default=30, cast=int)
BACKUP_STORAGE_PATH = config('BACKUP_STORAGE_PATH', default=os.path.join(BASE_DIR, 'backups'))

# Performance monitoring
ENABLE_PERFORMANCE_MONITORING = config('ENABLE_PERFORMANCE_MONITORING', default=True, cast=bool)
SLOW_QUERY_THRESHOLD = config('SLOW_QUERY_THRESHOLD', default=1.0, cast=float)  # seconds

# Security headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https: data:; connect-src 'self'; frame-ancestors 'self';"
}
