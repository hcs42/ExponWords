# This file is part of ExponWords.
#
# ExponWords is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# ExponWords is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# ExponWords.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2011 Csaba Hoch

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('ew.views',
    url(r'^$',
        view='index',
        name='index'),
    url(r'^word-pair/(?P<word_pair_id>\d+)/edit/$',
        view='edit_word_pair',
        name='edit_word_pair'),
    url(r'^dict/(?P<wdict_id>\d+)/$',
        view='wdict',
        name='wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/practice/$',
        view='practice_wdict',
        name='practice_wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/words-to-practice-today/$',
        view='get_words_to_practice_today',
        name='get_words_to_practice_today'),
    url(r'^dict/(?P<wdict_id>\d+)/update-word/$',
        view='update_word',
        name='update_word'),
    url(r'^delete-word-pairs/$',
        view='delete_word_pairs',
        name='delete_word_pairs'),
    url(r'^dict/(?P<wdict_id>\d+)/view/$',
        view='view_wdict',
        name='view_wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/add-word-pair/$',
        view='add_word_pair',
        name='add_word_pair'),
    url(r'^dict/(?P<wdict_id>\d+)/import-word-pairs-from-text/$',
        view='import_word_pairs_from_text',
        name='import_word_pairs_from_text'),
    url(r'^dict/(?P<wdict_id>\d+)/export-word-pairs-to-text/$',
        view='export_word_pairs_to_text',
        name='export_word_pairs_to_text'),
    url(r'^dict/(?P<wdict_id>\d+)/import-word-pairs-from-tsv/$',
        view='import_word_pairs_from_tsv',
        name='import_word_pairs_from_tsv'),
    url(r'^dict/(?P<wdict_id>\d+)/delete/$',
        view='delete_wdict',
        name='delete_wdict'),
    url(r'^create-dict/$',
        view='add_wdict',
        name='add_wdict'),
    url(r'^search/$',
        view='search',
        name='search'),
    url(r'^options/$',
        view='options',
        name='options'),
    url(r'^help/(?P<lang>[a-zA-Z-]+)/.*',
        view='help',
        name='help'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r'^login/$',
        view='login',
        name='login'),
    url(r'^logout/$',
        view='logout',
        kwargs={'next_page': '..'},
        name='logout'),
)
urlpatterns += patterns('',
    url(r'^i18n/',
        view=include('django.conf.urls.i18n'),
        name='i18n'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$',
         'django.views.static.serve',
         {'document_root': settings.STATIC_DOC_ROOT}),
    )
