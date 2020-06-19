"""
Django settings for invoices project.

Generated by 'django-admin startproject' using Django 1.8.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pc_pf1h+5n4h(ayu2)j@2_c+qgumxfa5xeplar6*eq8x745lg!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Do not Allow all host headers
# TODO: fix this hard coded value
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.sur.lu', '.herokuapp.com']

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'dal',
    'dal_select2',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gdstorage',
    'rest_framework',
    'rest_framework.authtoken',
    'constance',
    'constance.backends.database',
    'invoices',
    'api',
    'corsheaders',
    # 'debug_toolbar'
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.auth.middleware.RemoteUserMiddleware',
    'django_currentuser.middleware.ThreadLocalUserMiddleware',
)

ROOT_URLCONF = 'invoices.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'invoices.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
# Parse database configuration from $DATABASE_URL
import dj_database_url

DATABASES = {'default': dj_database_url.config(default='postgres://inur:inur@localhost:5432/inur')}
if 'CIRCLECI' in os.sys.argv:
    DATABASES['default'] = dj_database_url.config(default='postgresql://root@localhost/circle_test?sslmode=disable')

# Enable Connection Pooling
# DATABASES['default']['ENGINE'] = 'django_postgrespool'
DATABASES['default']['AUTOCOMMIT'] = True

# DATABASES = {
#     'default': {        
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'django_db',
#         'USER' : 'user_name',
#         'PASSWORD' : 'password',
#         'HOST' : '127.0.0.1',
#         'PORT' : '5432',
#     }
# }


# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static asset configuration
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static/'),
)

MEDIA_ROOT = os.path.join(BASE_DIR, '../media')
MEDIA_URL = '/media/'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'fr-be'

TIME_ZONE = 'Europe/Luxembourg'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

COUNTRIES_FIRST = ['LU', 'FR', 'BE', 'DE']
COUNTRIES_FIRST_BREAK = '...'

CONSTANCE_ADDITIONAL_FIELDS = {
    'yes_no_null_select': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((None, "..."), (True, "Oui"), (False, "Non"))
    }],
}

CONSTANCE_CONFIG = {
    'AT_HOME_CARE_CODE': (
        'NF01', "CareCode that is set to Prestation's copy which is created if at_home is checked", str),
    'MAIN_NURSE_CODE': (
        '300744-44', "Code infirmier pour les soins", str),
    'MAIN_BANK_ACCOUNT': (
        'LU55 0019 4555 2516 1000 BCEELULL', "Compte bancaire IBAN pour les virement bancaire ", str),
    'ALTERNATE_BANK_ACCOUNT': (
        'LUXX XXXX XXXX XXXX XXXX XXXXLULL', "Compte bancaire n.2 IBAN pour les virement bancaire ", str),
    'NURSE_NAME':
        ('Regine SIMBA',
         'Nom du prestataire de soins (apparaît sur les factures)', str),
    'NURSE_ADDRESS':
        ('1A, rue fort wallis',
         'Adresse du prestataire de soins (apparait sur les factures)', str),
    'NURSE_ZIP_CODE_CITY':
        ('L-2714 Luxembourg',
         'Code postal et Ville du prestataire de soins (apparait sur les factures)', str),
    'NURSE_PHONE_NUMBER':
        ('Tél: 691.30.85.84',
         'Nom et adresse du prestataire de soins (apparait sur les factures)', str),
    'USE_GDRIVE': (False, 'Utilisation de Google Drive et Google Calendar', 'yes_no_null_select')
}

CONSTANCE_CONFIG_FIELDSETS = {
    'Options Générales': ('USE_GDRIVE', 'AT_HOME_CARE_CODE'),
    'Options de Facturation': ('MAIN_NURSE_CODE', 'NURSE_NAME', 'NURSE_ADDRESS', 'NURSE_ZIP_CODE_CITY',
                               'NURSE_PHONE_NUMBER', 'MAIN_BANK_ACCOUNT', 'ALTERNATE_BANK_ACCOUNT'),
}

GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE = os.path.join(BASE_DIR, '../keys/gdrive_storage_key.json')
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ and not os.path.exists(GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE):
    credentials = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    with open(GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE, 'w') as outfile:
        json.dump(json.loads(credentials), outfile)

INTERNAL_IPS = {'127.0.0.1', }

IMPORTER_CSV_FOLDER = os.path.join(BASE_DIR, '../initialdata/')

CORS_ORIGIN_WHITELIST = [
    'http://localhost:4200',
]

if 'EMAIL_HOST' in os.environ:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ['EMAIL_HOST']
    EMAIL_USE_TLS = True
    EMAIL_PORT = 587
    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
