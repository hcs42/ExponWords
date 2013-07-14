# Copyright (C) 2011-2013 Csaba Hoch
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('ew.views',

    # Index view
    url(r'^$',
        view='index',
        name='index'),

    # Views when logged out
    url(r'^register/$',
        view='register',
        name='register'),
    url(r'^lang/$',
        view='language',
        name='language'),
    url(r'^help/(?P<lang>[a-zA-Z-]+)/$',
        view='help',
        name='help'),
    url(r'^help/(?P<lang>[a-zA-Z-]+)/(?P<page>[a-zA-Z0-9_-]+)/$',
        view='docs',
        name='docs'),

    # Views when logged in
    url(r'^dict/(?P<wdict_id>\d+)/$',
        view='wdict',
        name='wdict'),
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
    url(r'^dict/(?P<wdict_id>\d+)/modify/$',
        view='modify_wdict',
        name='modify_wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/delete/$',
        view='delete_wdict',
        name='delete_wdict'),
    url(r'^create-dict/$',
        view='add_wdict',
        name='add_wdict'),
    url(r'^visualize/$',
        view='visualize',
        name='visualize'),
    url(r'^settings/$',
        view='ew_settings',
        name='ew_settings'),

    # Practice
    url(r'^dict/(?P<wdict_id>\d+)/practice/$',
        view='practice_wdict',
        name='practice_wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/practice_early/$',
        view='practice_wdict_early',
        name='practice_wdict_early'),
    url(r'^practice/$',
        view='practice',
        name='practice'),
    url(r'^dict/(?P<wdict_id>\d+)/words-to-practice-today/$',
        view='get_words_to_practice_today',
        name='get_words_to_practice_today'),

    # Search and operations
    url(r'^search/$',
        view='search',
        name='search'),
    url(r'^word-pair/(?P<word_pair_id>\d+)/edit/$',
        view='edit_word_pair',
        name='edit_word_pair'),
    url(r'^dict/update-word/$',
        view='update_word',
        name='update_word'),
    url(r'^dict/add-label/$',
        view='add_label',
        name='add_label'),
    url(r'^operation-on-word-pairs/$',
        view='operation_on_word_pairs',
        name='operation_on_word_pairs'),

    # Staff views
    url(r'^announce_release/$',
        view='announce_release',
        name='announce_release'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r'^login/$',
        view='login',
        name='login',
        kwargs={'template_name': 'ew/login.html'}),
    url(r'^logout/$',
        view='logout',
        kwargs={'next_page': '..'},
        name='logout'),
    url(r'^change-password/$',
        view='password_change',
        name='password_change',
        kwargs={'template_name': 'ew/registration/password_change_form.html'}),
    url(r'^change-password/done/$',
        view='password_change_done',
        name='password_change_done',
        kwargs={'template_name': 'ew/registration/password_change_done.html'}),
    url(r'^reset-password/$',
        view='password_reset',
        name='password_reset',
        kwargs={'template_name': 'ew/registration/password_reset_form.html',
                'email_template_name': 'ew/registration/password_reset_email.html'}),
    url(r'^reset-password/(?P<uidb36>[0-9A-Za-z]{1,13})-'
        r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        view='password_reset_confirm',
        name='password_reset_confirm',
        kwargs={'template_name': 'ew/registration/password_reset_confirm.html'}),
    url(r'^reset-password/done/$',
        view='password_reset_done',
        name='password_reset_done',
        kwargs={'template_name': 'ew/registration/password_reset_done.html'}),
    url(r'^reset-password/complete/$',
        view='password_reset_complete',
        name='password_reset_complete',
        kwargs={'template_name': 'ew/registration/password_reset_complete.html'}),
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
