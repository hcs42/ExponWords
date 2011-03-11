from settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STATIC_DOC_ROOT = '/home/hcs/ExponWords/ew/media'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/home/hcs/ExponWords/dev.db',
    }
}
