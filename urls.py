from django.conf.urls.defaults import *
from ExponWords import settings

urlpatterns = patterns('ew.views',
    (r'^$', 'index'),
    #(r'^(?P<poll_id>\d+)/$', 'menu'),
    #(r'^(?P<poll_id>\d+)/results/$', 'results'),
    #(r'^(?P<poll_id>\d+)/vote/$', 'vote'),
)

urlpatterns += patterns('django.contrib.auth.views',
    (r'^login/$', 'login'),
    (r'^logout/$', 'logout', {'next_page': '..'}),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$',
         'django.views.static.serve',
         {'document_root': settings.STATIC_DOC_ROOT}),
    )
