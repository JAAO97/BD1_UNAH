import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ticketmaster-rd-2025-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # NO agregamos 'django.contrib.auth' ni apps con models
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'ticketmaster_rd.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'app' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ticketmaster_rd.wsgi.application'

DATABASES = { }  

LANGUAGE_CODE = 'es-do'
TIME_ZONE = 'America/Santo_Domingo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_ENGINE = 'django.contrib.sessions.backends.file'  