from django.urls import include, re_path
from django.urls import re_path as url
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
