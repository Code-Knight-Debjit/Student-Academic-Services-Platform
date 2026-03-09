"""
Django settings for Student Results System.
"""

from pathlib import Path
from decouple import config, Csv
import os
from dotenv import load_dotenv

load_dotenv()
# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS can be provided as a comma-separated string in the .env file.
# Example: ALLOWED_HOSTS=localhost,127.0.0.1,.example.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

CSRF_TRUSTED_ORIGINS = [
    "https://debjit-paul.me",
    "https://www.debjit-paul.me"
]
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local apps
    'core',
    'results',
    'accounts',
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

ROOT_URLCONF = 'student_results.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'results.context_processors.notification_counts',
                'results.context_processors.exam_configurations',
                'results.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'student_results.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# STATIC_URL = '/staticfiles/'
# STATIC_ROOT = BASE_DIR / 'staticfiles'
# STATICFILES_DIRS = ['app/staticfiles']
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Razorpay Configuration
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='')
RAZORPAY_WEBHOOK_SECRET = config('RAZORPAY_WEBHOOK_SECRET', default='')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

import os
os.makedirs(MEDIA_ROOT / 'receipts' / 'revaluation', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'receipts' / 'makeup_exam', exist_ok=True)
os.makedirs(MEDIA_ROOT / 'hall_tickets', exist_ok=True)
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google reCAPTCHA
RECAPTCHA_SITE_KEY = config('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = config('RECAPTCHA_SECRET_KEY', default='')

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/admin-panel/'
LOGOUT_REDIRECT_URL = '/'

REDIS_URL = config("REDIS_URL", default="")
REDIS_URL_2 = config("REDIS_URL_2", default="")
# settings.py
if REDIS_URL:

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True,
                },
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "SERIALIZER": "django_redis.serializers.pickle.PickleSerializer",
            },
            "KEY_PREFIX": "",
            "VERSION": 1,
            "KEY_FUNCTION": "results.cache.make_key",
            "TIMEOUT": 60 * 30,
        },
        "sessions": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL_2,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True,
                },
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "SERIALIZER": "django_redis.serializers.pickle.PickleSerializer",
            },
            "KEY_PREFIX": "session",
            "VERSION": 1,
        },
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "sessions"
else:
    # Fallback for local dev without Redis
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "sasp-locmem",
        }
    }

    
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Your existing Django logger (keep as-is)
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        # New: cache layer — set to DEBUG locally, INFO in production
        "results.cache": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "results.signals": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

RATELIMIT_ENABLE = False
