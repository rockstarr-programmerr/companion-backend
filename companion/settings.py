"""
Django settings for companion project.

Generated by 'django-admin startproject' using Django 3.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import sys
from datetime import timedelta
from pathlib import Path

import environ
from email.utils import getaddresses

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


env = environ.Env(
    SECRET_KEY=(str, 'nothingtoseehere'),
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, []),

    # If you want to use unsafe characters in DATABASE_URL, you must escape it first using urllib.parse.quote
    # Example: if your db password is xyz#$%abc, then your DATABASE_URL should be:
    # mysql://user:xyz%23%24%25abc@mysql:3306/dbname
    DATABASE_URL=(str, 'sqlite:///db.sqlite3'),

    CORS_ALLOWED_ORIGINS=(list, [
        'http://localhost:8080',
        'http://127.0.0.1:8080',
    ]),
    ALLOWED_DEEPLINKS=(list, [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]),
    ADMINS=(list, []),
    USE_X_FORWARDED_HOST=(bool, False),

    EMAIL_BACKEND=(str, 'django.core.mail.backends.filebased.EmailBackend'),
    EMAIL_FILE_PATH=(str, BASE_DIR / 'temp' / 'sent_emails'),
    EMAIL_HOST=(str, ''),
    EMAIL_PORT=(str, ''),
    EMAIL_USE_SSL=(bool, True),
    EMAIL_USE_TLS=(bool, False),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    DEFAULT_FROM_EMAIL=(str, ''),

    SOCIALACCOUNT_APP_USE_ENV=(bool, True),
    SOCIALACCOUNT_GOOGLE_CLIENT_ID=(str, ''),
    SOCIALACCOUNT_GOOGLE_SECRET=(str, ''),
    SOCIALACCOUNT_GOOGLE_KEY=(str, ''),
    SOCIALACCOUNT_FACEBOOK_CLIENT_ID=(str, ''),
    SOCIALACCOUNT_FACEBOOK_SECRET=(str, ''),
    SOCIALACCOUNT_FACEBOOK_KEY=(str, ''),

    CELERY_BROKER_URL=(str, 'amqp://companion_user:companion_password@localhost:5672/companion_vhost'),
)
# reading .env file
env_file = str(BASE_DIR / '.env')
environ.Env.read_env(env_file=env_file)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'crispy_forms',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'user.apps.UserConfig',
    'split_the_bill.apps.SplitTheBillConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'companion.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'companion.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': env.db(),
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'user.User'

CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')

CSRF_COOKIE_NAME = 'csrftokencompanion'

USE_X_FORWARDED_HOST = env('USE_X_FORWARDED_HOST')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For authentication to browsable API
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/min',
        'user': '60/min'
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'companion.renderers.CustomBrowsableAPIRenderer',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,  # Needed for invalidating used password reset token

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_ROOT = BASE_DIR / 'staticfiles'

LOGIN_REDIRECT_URL = '/'

PASSWORD_RESET_TIMEOUT = 30 * 60  # 30 minutes

ADMINS = getaddresses(env('ADMINS'))

ALLOWED_DEEPLINKS = env('ALLOWED_DEEPLINKS')

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_FILE_PATH = env('EMAIL_FILE_PATH')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_SSL = env('EMAIL_USE_SSL')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'FIELDS': [
            'id',
            'email',
            'first_name',
            'last_name',
            'middle_name',
            'name',
            'name_format',
            'picture',
            'short_name',
        ],
        'VERIFIED_EMAIL': True,
        'VERSION': 'v11.0',
    }
}

if env('SOCIALACCOUNT_APP_USE_ENV'):
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': env('SOCIALACCOUNT_GOOGLE_CLIENT_ID'),
        'secret': env('SOCIALACCOUNT_GOOGLE_SECRET'),
        'key': env('SOCIALACCOUNT_GOOGLE_KEY'),
    }
    SOCIALACCOUNT_PROVIDERS['facebook']['APP'] = {
        'client_id': env('SOCIALACCOUNT_FACEBOOK_CLIENT_ID'),
        'secret': env('SOCIALACCOUNT_FACEBOOK_SECRET'),
        'key': env('SOCIALACCOUNT_FACEBOOK_KEY'),
    }

CELERY_BROKER_URL = env('CELERY_BROKER_URL')

IS_TESTING = 'test' in sys.argv

if IS_TESTING:
    if 'DEFAULT_THROTTLE_RATES' in REST_FRAMEWORK:
        del REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
