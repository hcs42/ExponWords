from django.conf.urls import include, url
from django.contrib import admin

from ExponWords import settings
import ew.urls

if settings.SCRIPT_NAME:
    prefix = settings.SCRIPT_NAME + '/'
else:
    prefix = ''

urlpatterns = [
    url(r'^' + prefix + 'admin/', admin.site.urls),
    url(r'^' + prefix, include(ew.urls)),
]
