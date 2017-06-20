import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'nago.settings'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from whitenoise.django import DjangoWhiteNoise
application = DjangoWhiteNoise(application)