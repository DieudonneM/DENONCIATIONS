"""
Django settings for denunciations_app project.
"""

from pathlib import Path

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

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

USE_SQLITE = config('USE_SQLITE', default=True, cast=bool)

# Application definition
INSTALLED_APPS = [
    'cloudinary_storage',
    'cloudinary',
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
USE_SQLITE = config('USE_SQLITE', default=not IS_PRODUCTION, cast=bool)

# 1. Si on est sur Render avec une base PostgreSQL configurée
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600
        )
    }
# 2. Sinon, on utilise la configuration locale (SQLite ou Postgres local)
elif USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='denunciations_app'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='127.0.0.1'),
            'PORT': config('DB_PORT', default='5432'),
        }
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
#STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / 'users' / 'static',
    BASE_DIR / 'denunciations' / 'static',
    BASE_DIR / 'core' / 'static',
]

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage", 
        #"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",  
    },
}

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


WHITENOISE_MANIFEST_STRICT = False


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.hostinger.com' 
EMAIL_PORT = 465 
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

# Vos identifiants de domaine
EMAIL_HOST_USER = 'contact@denonciation-abus-rdc.net' 
EMAIL_HOST_PASSWORD = 'MHDkdeGBH66@@' 

# L'adresse qui s'affichera par défaut chez le destinataire
DEFAULT_FROM_EMAIL = "Ministère d'Emploi et Travail <contact@denonciation-abus-rdc.net>"
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.hostinger.com')
# Choose port according to provider: 587 for STARTTLS, 465 for SSL
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='contact@denonciation-abus-rdc.net')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
# Use TLS (STARTTLS) by default for port 587; set EMAIL_USE_SSL True if using port 465
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)

# Defaults for sender addresses and server errors
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default="Ministère d'Emploi et Travail <contact@denonciation-abus-rdc.net>")
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

# Admins that receive server error emails (500)
ADMINS = tuple(config('ADMINS', default='', cast=Csv()))

# IMAP/POP settings (for receiving/fetching mails from an external mailbox)
# These are optional and used by any custom mail polling/processing scripts you run.
IMAP_HOST = config('IMAP_HOST', default='imap.hostinger.com')
IMAP_PORT = config('IMAP_PORT', default=993, cast=int)
IMAP_USE_SSL = config('IMAP_USE_SSL', default=True, cast=bool)
IMAP_USER = config('IMAP_USER', default=EMAIL_HOST_USER)
IMAP_PASSWORD = config('IMAP_PASSWORD', default=EMAIL_HOST_PASSWORD)

