from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from ExponWords import settings

if settings.SCRIPT_NAME:
    prefix = settings.SCRIPT_NAME + '/'
else:
    prefix = ''

urlpatterns = patterns('',
    url(r'^' + prefix + 'admin/', include(admin.site.urls)),
    url(r'^' + prefix, include('ew.urls')),
)
