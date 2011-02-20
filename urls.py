from django.conf.urls.defaults import *
from ExponWords import settings

urlpatterns = patterns('ew.views',
    (r'^$', 'index'),
    (r'^word-pair/(?P<word_pair_id>\d+)/edit/$', 'edit_word_pair'),
    (r'^dict/(?P<wdict_id>\d+)/$', 'wdict'),
    (r'^dict/(?P<wdict_id>\d+)/view/$', 'view_wdict'),
    (r'^dict/(?P<wdict_id>\d+)/add-word-pair/$', 'add_word_pair'),
    (r'^create-dict/$', 'add_wdict'),
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
