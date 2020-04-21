import os
import tempfile

import environ
from django.utils.translation import gettext_lazy as _

env = environ.Env(DEBUG=(bool, False))

try:
    environ.Env.read_env(env.str('ENV_PATH', '.env'))
except:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

SECRET_KEY = env('MCE_SECRET_KEY', default='fa(=utzixi05twa3j*v$eaccuyq)!-_c-8=sr#hih^7i&xcw)^')

DEBUG = env('MCE_DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'django_filters',
    'django_extensions',

    'rest_framework',
    'rest_framework.authtoken',

    'django_rq',
    'mce_tasks_rq',
    'mce_django_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project_test.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        #'DIRS': [
        #     os.path.join(BASE_DIR, 'templates'),
        #],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
            #'loaders': [
            #    ('django.template.loaders.cached.Loader', [
            #        'django.template.loaders.filesystem.Loader',
            #        'django.template.loaders.app_directories.Loader',
            #    ])
            #],
        },
    },
]


WSGI_APPLICATION = 'project_test.wsgi.application'

#SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

CACHES = {
    "default": env.cache(default='redis://127.0.0.1:6379/0')
}

DATABASES = {
    'default': env.db(default='sqlite:////tmp/mce-tasks-rq-sqlite.db'),
}

AUTH_USER_MODEL = 'mce_django_app.User'

LOGIN_URL = 'admin:login'
#LOGIN_URL = '/accounts/login/'
#LOGIN_REDIRECT_URL = '/'

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


LOCALE_PATHS = ( os.path.join(BASE_DIR, 'locale'), )

LANGUAGES = [
  ('fr', _('Français')),
  ('en', _('Anglais')),
]

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_ROOT = tempfile.gettempdir()

SITE_ID = env('MCE_SITE_ID', default=1, cast=int)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'debug': {
            'format': '%(asctime)s - [%(name)s] - [%(process)d] - [%(module)s] - [line:%(lineno)d] - [%(levelname)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[%(process)d] - %(asctime)s - %(name)s: [%(levelname)s] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'debug'
        },
        #'db_log': {
        #    'class': 'mce_django_app.db_log_handler.DatabaseLogHandler'
        #},
    },
    'loggers': {
        '': {
            'handlers': ['console'], #'db_log'],
            'level': env('MCE_LOG_LEVEL', default='DEBUG'),
            'propagate': False,
        },
        'urllib3': {'level': 'ERROR'},
        'chardet': {'level': 'WARN'},
        'cchardet': {'level': 'WARN'},
    },
}


TEST_RUNNER = 'project_test.runner.PytestTestRunner'

RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
        #'HOST': 'localhost',
        #'PORT': 6379,
        #'DB': 0,
        #'PASSWORD': 'some-password',
        #'DEFAULT_TIMEOUT': 360,
    },
    #'low': {
    #    'USE_REDIS_CACHE': 'redis-cache',
        #'HOST': 'localhost',
        #'PORT': 6379,
        #'DB': 0,
    #}
}


RQ = {
    'DEFAULT_RESULT_TTL': 3600, # 1H
    'BURST': True,
    'SHOW_ADMIN_LINK': True
}

if DEBUG:
    for queueConfig in RQ_QUEUES.itervalues():
        queueConfig['ASYNC'] = False
