from django.conf.urls.defaults import *
from ExponWords import settings

urlpatterns = patterns('ew.views',
    (r'^$', 'index'),
    (r'^word-pair/(?P<word_pair_id>\d+)/edit/?$', 'edit_word_pair'),
    (r'^dict/(?P<wdict_id>\d+)/?$', 'wdict'),
    (r'^dict/(?P<wdict_id>\d+)/practice/?$', 'practice_wdict'),
    (r'^dict/(?P<wdict_id>\d+)/words-to-practice-today/?$',
     'get_words_to_practice_today'),
    (r'^dict/(?P<wdict_id>\d+)/update-word/?$', 'update_word'),
    (r'^dict/(?P<wdict_id>\d+)/view/?$', 'view_wdict'),
    (r'^dict/(?P<wdict_id>\d+)/add-word-pair/?$', 'add_word_pair'),
    (r'^dict/(?P<wdict_id>\d+)/import-word-pairs-from-text/?$',
     'import_word_pairs_from_text'),
    (r'^dict/(?P<wdict_id>\d+)/import-word-pairs-from-tsv/?$',
     'import_word_pairs_from_tsv'),
    (r'^dict/(?P<wdict_id>\d+)/delete/?$', 'delete_wdict'),
    (r'^create-dict/?$', 'add_wdict'),
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
