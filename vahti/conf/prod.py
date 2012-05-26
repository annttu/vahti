import os
import os.path
import json
import email.utils

from .base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'vahti.sqlite3',
    }
}

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/home/users/joneskoo/sites/joneskoo.kapsi.fi/secure-www/vahti-static/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# Private constants
with open(os.path.join(os.path.dirname(__file__), 'private.json')) as f:
    private = json.load(f)

SECRET_KEY = private['SECRET_KEY']

ADMINS = [email.utils.parseaddr(x) for x in private['ADMIN_EMAIL']]
MANAGERS = ADMINS
