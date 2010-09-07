DEBUG = True

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'katipo.db'
DATABASE_OPTIONS = {'timeout': 30} 

ROOT_URLCONF = 'katipo.urls'

MEDIA_ROOT = './katipo/media/'
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media_admin/'

INSTALLED_APPS = (
    'katipo',
    'django.contrib.sessions',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)
