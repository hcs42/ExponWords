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

# Copyright (C) 2011-2012 Csaba Hoch

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
    url(r'^practice/$',
        view='practice',
        name='practice'),

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
        name='login'),
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
