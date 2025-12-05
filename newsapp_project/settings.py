from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-replace-this-for-production'
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST API framework
    'rest_framework',

    # Your main app
    'sabuzz',

    'widget_tweaks',
]

# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',   # required
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # required
    'django.contrib.messages.middleware.MessageMiddleware',     # required
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # <-- NO context processor here. Only middleware classes belong in MIDDLEWARE.
]

ROOT_URLCONF = 'newsapp_project.urls'

# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'sabuzz' / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # custom context processors (add both here)
                'sabuzz.context_processors.user_roles',
                'sabuzz.context_processors.global_weather',
            ],
        },
    },
]

WSGI_APPLICATION = 'newsapp_project.wsgi.application'

# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================================
# AUTH + LOGIN
# ============================================================

AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = '/login/'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True

# ============================================================
# STATIC + MEDIA
# ============================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'sabuzz' / 'static'
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ============================================================
# DJANGO REST FRAMEWORK (IMPORTANT)
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # browser login
    ],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================
# WEATHER API CONFIGURATION
# ============================================================
OPENWEATHER_API_KEY=os.getenv('OPENWEATHER_API_KEY')