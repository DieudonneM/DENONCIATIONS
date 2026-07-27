"""
Django settings for denunciations_app project.
"""

from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

from decouple import config
import os
from decouple import Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment detection
ENVIRONMENT = config('ENVIRONMENT', default='local').lower()
IS_PRODUCTION = ENVIRONMENT == 'production'

# Security & Keys
SECRET_KEY = config('SECRET_KEY', default='django-insecure-rdc-ministry-work-incidents-reporting-platform')

DEBUG = config('DEBUG', default=not IS_PRODUCTION, cast=bool)

if DEBUG:
    ALLOWED_HOSTS = config(
        'ALLOWED_HOSTS',
        default='127.0.0.1,localhost,denonciation-abus-rdc.net',
        cast=Csv(),
    )
else:
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='denonciation-abus-rdc.net', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',          # Gestion des utilisateurs
    'denunciations',  # Gestion des dénonciations
    'core',           # Application principale
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'denunciations_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'users' / 'templates',
            BASE_DIR / 'denunciations' / 'templates',
            BASE_DIR / 'core' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'denunciations_app.wsgi.application'

# Database Configuration
RENDER_DATABASE_URL = config(
    'RENDER_DATABASE_URL',
    default=config('DATABASE_URL', default=''),
).strip()

if not RENDER_DATABASE_URL:
    raise ImproperlyConfigured(
        'RENDER_DATABASE_URL (ou DATABASE_URL) est obligatoire: la base Render est requise pour tous les environnements.'
    )

DATABASES = {
    'default': dj_database_url.parse(
        RENDER_DATABASE_URL,
        conn_max_age=600,
        ssl_require=True,
    )
}

# Security settings for production
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
    }
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-FR'

TIME_ZONE = 'Africa/Kinshasa'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / 'users' / 'static',
    BASE_DIR / 'denunciations' / 'static',
    BASE_DIR / 'core' / 'static',
]

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Backends d'authentification
AUTHENTICATION_BACKENDS = [
    'users.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Login settings
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
