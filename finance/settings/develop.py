# -*- coding: utf-8 -*-
"""
    Настройки среды для разработки
"""
from . import *  # NOQA


ALLOWED_HOSTS = ['finance.dev']

SITE_ID = 1

DEBUG = True

COMPRESS_ENABLED = not DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'postgres.local',
        'PORT': ''
    }
}

INSTALLED_APPS += (  # NOQA
    'debug_toolbar',
)

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE  # NOQA


def show_toolbar(request):
    if request.is_ajax():
        return False
    return True

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'finance.settings.develop.show_toolbar',
}
