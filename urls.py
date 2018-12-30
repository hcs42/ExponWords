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

from django.conf.urls import include, url
from django.conf import settings
import django.conf.urls.i18n
import django.contrib.auth.views

import ew.views as views

urlpatterns = [

    # Index view
    url(r'^$',
        view=views.index,
        name='index'),

    # Views when logged out
    url(r'^register/$',
        view=views.register,
        name='register'),
    url(r'^lang/$',
        view=views.language,
        name='language'),
    url(r'^help/(?P<lang>[a-zA-Z-]+)/$',
        view=views.help,
        name='help'),
    url(r'^help/(?P<lang>[a-zA-Z-]+)/(?P<page>[a-zA-Z0-9_-]+)/$',
        view=views.docs,
        name='docs'),

    # Views when logged in
    url(r'^dict/(?P<wdict_id>\d+)/$',
        view=views.wdict,
        name='wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/add-word-pair/$',
        view=views.add_word_pair,
        name='add_word_pair'),
    url(r'^dict/(?P<wdict_id>\d+)/import-word-pairs-from-text/$',
        view=views.import_word_pairs_from_text,
        name='import_word_pairs_from_text'),
    url(r'^dict/(?P<wdict_id>\d+)/export-word-pairs-to-text/$',
        view=views.export_word_pairs_to_text,
        name='export_word_pairs_to_text'),
    url(r'^dict/(?P<wdict_id>\d+)/import-word-pairs-from-tsv/$',
        view=views.import_word_pairs_from_tsv,
        name='import_word_pairs_from_tsv'),
    url(r'^dict/(?P<wdict_id>\d+)/modify/$',
        view=views.modify_wdict,
        name='modify_wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/delete/$',
        view=views.delete_wdict,
        name='delete_wdict'),
    url(r'^create-dict/$',
        view=views.add_wdict,
        name='add_wdict'),
    url(r'^visualize/$',
        view=views.visualize,
        name='visualize'),
    url(r'^settings/$',
        view=views.ew_settings,
        name='ew_settings'),
    url(r'^settings/x$',
        view=views.ew_settings_x,
        name='ew_settings_x'),

    # Practice
    url(r'^dict/(?P<wdict_id>\d+)/practice/$',
        view=views.practice_wdict,
        name='practice_wdict'),
    url(r'^dict/(?P<wdict_id>\d+)/practice_early/$',
        view=views.practice_wdict_early,
        name='practice_wdict_early'),
    url(r'^practice/$',
        view=views.practice,
        name='practice'),
    url(r'^dict/(?P<wdict_id>\d+)/words-to-practice-today/$',
        view=views.get_words_to_practice_today,
        name='get_words_to_practice_today'),

    # Search and operations
    url(r'^search/$',
        view=views.search,
        name='search'),
    url(r'^word-pair/(?P<word_pair_id>\d+)/edit/$',
        view=views.edit_word_pair,
        name='edit_word_pair'),
    url(r'^dict/update-word/$',
        view=views.update_word,
        name='update_word'),
    url(r'^dict/add-label/$',
        view=views.add_label,
        name='add_label'),
    url(r'^operation-on-word-pairs/$',
        view=views.operation_on_word_pairs,
        name='operation_on_word_pairs'),

    # Staff views
    url(r'^announce_release/$',
        view=views.announce_release,
        name='announce_release'),
]

urlpatterns += [
    url(r'^login/$',
        view=django.contrib.auth.views.login,
        name='login',
        kwargs={'template_name': 'ew/login.html'}),
    url(r'^logout/$',
        view=django.contrib.auth.views.logout,
        kwargs={'next_page': '..'},
        name='logout'),
    url(r'^change-password/$',
        view=django.contrib.auth.views.password_change,
        name='password_change',
        kwargs={'template_name': 'ew/registration/password_change_form.html'}),
    url(r'^change-password/done/$',
        view=django.contrib.auth.views.password_change_done,
        name='password_change_done',
        kwargs={'template_name': 'ew/registration/password_change_done.html'}),

    # This how how password reset works:
    # password_reset_form -> POST
    # (send) -> password_reset_email
    # (redirect) -> password_reset_done
    #
    # (email link) -> password_reset_confirm -> POST
    # (redirect) -> password_reset_complete
    url(r'^reset-password/$',
        view=django.contrib.auth.views.password_reset,
        name='password_reset',
        kwargs={'template_name': 'ew/registration/password_reset_form.html',
                'email_template_name': 'ew/registration/password_reset_email.html'}),
    url(r'^reset-password/done/$',
        view=django.contrib.auth.views.password_reset_done,
        name='password_reset_done',
        kwargs={'template_name': 'ew/registration/password_reset_done.html'}),
    url(r'^reset-password/complete/$',
        view=django.contrib.auth.views.password_reset_complete,
        name='password_reset_complete',
        kwargs={'template_name': 'ew/registration/password_reset_complete.html'}),
    url(r'^reset-password/(?P<uidb64>[0-9A-Za-z]{1,13})-'
        r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        view=django.contrib.auth.views.password_reset_confirm,
        name='password_reset_confirm',
        kwargs={'template_name': 'ew/registration/password_reset_confirm.html'}),
]

urlpatterns += [
    url(r'^i18n/',
        view=include(django.conf.urls.i18n),
        name='i18n'),
]
