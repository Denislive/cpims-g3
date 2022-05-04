"""
Django settings for cpims project.

Generated by 'django-admin startproject' using Django 1.8.4.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'h34yo5l8c8!edb%^b@3j-i^gc$e)fcjnw_9jm4a^%jbq&*41+@'

FORM_RENDERER = 'django.forms.renderers.DjangoTemplates'


ALLOWED_HOSTS = ['*']

cpims_db_host = os.environ.get(
    'CPIMS_HOST') if os.environ.get('CPIMS_HOST') else '127.0.0.1'
cpims_db_pass = os.environ.get(
    'CPIMS_PASSWORD') if os.environ.get('CPIMS_PASSWORD') else 'Xaen!ee8'
cpims_db_instance = os.environ.get(
    'CPIMS_DB') if os.environ.get('CPIMS_DB') else 'cpims'
cpims_db_port = os.environ.get(
    'CPIMS_PORT') if os.environ.get('CPIMS_PORT') else '5432'
cpims_db_user = os.environ.get(
    'CPIMS_DBUSER') if os.environ.get('CPIMS_DBUSER') else 'cpimsdbuser'
cpims_debug = eval(os.environ.get(
    'CPIMS_DEBUG')) if os.environ.get('CPIMS_DEBUG') else True

DEBUG = cpims_debug

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cpovc_main',
    'cpovc_auth',
    'cpovc_registry',
    'cpovc_forms',
    'cpovc_gis',
    'cpovc_access',
    'cpovc_settings',
    'crispy_forms',
    'cpovc_ovc',
    'import_export',
    'rest_framework',
    'data_cleanup',
    'cpovc_offline_mode',
    'cpovc_manage',
    'forums',
    'adminsortable',
    'simple_forums',
     'cpovc_manage',
    'notifications',
    'cpovc_help',
    'cpovc_pfs',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'cpovc_access.middleware.AuthenticationPolicyMiddleware',
    # 'cpovc_auth.middleware.UserRestrictMiddleware',
    # 'cpovc_access.middleware.FailedLoginMiddleware',

]

ROOT_URLCONF = 'cpims.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(BASE_DIR, 'templates')), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cpovc_main.context_processors.global_settings',
                'simple_forums.context_processors.installed_apps',
                
            ],
        },
    },
]

WSGI_APPLICATION = 'cpims.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': cpims_db_instance,
        'USER': cpims_db_user,
        'PASSWORD': cpims_db_pass,
        'HOST': cpims_db_host,
        'PORT': cpims_db_port, },
    'reporting': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': cpims_db_instance,
        'USER': cpims_db_user,
        'PASSWORD': cpims_db_pass,
        'HOST': '41.89.94.104',
        'PORT': cpims_db_port, }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

DOCUMENTS_URL = '/documents/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'reports')

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"), )

AUTH_USER_MODEL = 'cpovc_auth.AppUser'

# AUTHENTICATION_BACKENDS = ['cpovc_auth.backends.CPOVCAuthenticationBackend']
# AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOW_NATIONAL_ID_LOGIN = True

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# to find out what this does
IS_CAPTURE_SITE = False

GIT_ROOT = ''

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

EMAIL_USE_TLS = True
EMAIL_HOST = ''
EMAIL_PORT = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

# Session variables
SESSION_COOKIE_AGE = 3 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

AXES_LOCKOUT_TEMPLATE = 'locked.html'
AXES_COOLOFF_TIME = 0.25

PASSWORD_CHANGE_POLICIES = (
    ('cpovc_access.password_change.PasswordChangeExpired', {}),
    ('cpovc_access.password_change.PasswordChangeTemporary', {}),
)

PASSWORD_STRENGTH_POLICIES = (
    ('cpovc_access.password_strength.PasswordMinLength', {}),
    ('cpovc_access.password_strength.PasswordContainsUpperCase', {}),
    ('cpovc_access.password_strength.PasswordContainsLowerCase', {}),
    ('cpovc_access.password_strength.PasswordContainsNumbers', {}),
    ('cpovc_access.password_strength.PasswordContainsSymbols', {}),
    ('cpovc_access.password_strength.PasswordUserAttrs', {}),
    ('cpovc_access.password_strength.PasswordLimitReuse', {}),
    ('cpovc_access.password_strength.PasswordDisallowedTerms', {
        'terms': ['cpims']
    }),
)

AUTHENTICATION_POLICIES = (
    ('cpovc_access.authentication.AuthenticationBasicChecks', {}),
    ('cpovc_access.authentication.AuthenticationDisableExpiredUsers', {}),
)

DOCUMENT_ROOT = os.path.join(BASE_DIR, 'templates/documents')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
CSRF_FAILURE_VIEW = 'cpims.views.csrf_failure'

OFFLINE_MODE_CAPABILITY_ENABLED = eval(
    os.environ.get('CAN_WORK_OFFLINE', 'True'))

# kmhfl API
KMHFL_USERNAME = '10004'
KMHFL_PASSWORD = 'public'
KMHFL_SCOPE = 'read'
KMHFL_CLIENTID = ''
KMHFL_CLIENT_SECRET = ''
KMHFL_API_BASE_URL = ''
KMHFL_FACILITY_BASE_URL = ''
KMHFL_LOGIN_URL = ''
KMHFL_GRANT_TYPE = ''
KMHFL_SUBCOUNTY_BASE_URL = ''
KMHFL_TOKEN_URL = ''

# nascop API
NASCOP_API_BASE_URL = os.environ.get(
    'NASCOP_API_BASE_URL') if os.environ.get('NASCOP_API_BASE_URL') else ''
NASCOP_LOGIN_URL = os.environ.get(
    'NASCOP_LOGIN_URL') if os.environ.get('NASCOP_LOGIN_URL') else ''
NASCOP_EMAIL = os.environ.get(
    'NASCOP_EMAIL') if os.environ.get('NASCOP_EMAIL') else ''
NASCOP_PASSWORD = os.environ.get(
    'NASCOP_PASSWORD') if os.environ.get('NASCOP_PASSWORD') else ''


STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
