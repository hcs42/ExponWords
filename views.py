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

import datetime
import functools
import json
import os
import random
import re
import sys
import traceback
import unicodedata
import urllib
import urlparse

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseServerError, \
                        HttpResponseBadRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import Context, loader
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
import django.db
import django.utils.translation

from ExponWords.ew.models import WordPair, WDict
import ExponWords.ew.models as models


##### Constants #####

ADD_WORD_PAIR_DATE_REMEMBER_SECONDS = 3600 # 1 hour
PRACTICE_WORD_ORDER_CHOICES = \
    [('random', _('Totally random')),
     ('zero_first', _('New and forgotten words first')),
     ('dimmer_first', _('I am a little behind')),
     ('dimmer_last', _('Relearn old words'))]
STRENGTHENER_METHOD_CHOICES = \
    [('double', _('Double')),
     ('proportional', _('Proportional'))]
PRACTICE_WORD_COUNT_LIMIT = 200


##### General helper functions #####


def set_lang_fun(request):
    lang = models.get_ewuser(request.user).lang
    request.session['django_language'] = lang
    django.utils.translation.activate(lang)


#### Helper functions > URLs and queries #####


def bad_unicode_to_str(u):
    """This function converts a unicode object that actually contains UTF-8
    encoded text (instead of unicode characters) to a UTF-8 encoded string."""
    return ''.join([chr(ord(ch)) for ch in u])


def remove_query_param(url, param_name):
    url_list = list(urlparse.urlparse(url))
    query_list = urlparse.parse_qsl(url_list[4], keep_blank_values=True)
    new_query_list = [(k, bad_unicode_to_str(v))
                      for k, v in query_list if k != param_name]
    new_raw_query = urllib.urlencode(new_query_list)
    url_list[4] = new_raw_query
    new_url = urlparse.urlunparse(url_list)
    return new_url


def normalize_string(s):
    # Code copied from: http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string/518232#518232
    return ''.join((c for c in unicodedata.normalize('NFD', s.lower())
                    if unicodedata.category(c) != 'Mn'))


##### Forms #####

class LenientChoiceField(forms.ChoiceField):

    def __init__(self, *args, **kw):
        super(LenientChoiceField, self).__init__(*args, **kw)

    def validate(self, value):
        super(forms.ChoiceField, self).validate(value)
        if value and not self.valid_value(value):
            self.is_really_valid = False
        else:
            self.is_really_valid = True


def create_WDictForm():
    # This class needs to be dynamically generated because of the lazy
    # translation (see commit 44900082b9).

    practice_word_order_choices = \
        [('default',
         _('Default (use the word order in the Settings page)'))] + \
         PRACTICE_WORD_ORDER_CHOICES

    strengthener_method_choices = \
        [('default',
         _('Default (use the strengthener method in the Settings page)'))] + \
         STRENGTHENER_METHOD_CHOICES

    class WDictForm(forms.Form):
        name = forms.CharField(max_length=255,
                               label=_("Name of the dictionary") + ':')
        lang1 = forms.CharField(max_length=255,
                                label=_("Language 1") + ':')
        lang2 = forms.CharField(max_length=255,
                                label=_("Language 2") + ':')
        practice_word_order = \
            forms.ChoiceField(
                choices=practice_word_order_choices,
                label=_('Practice page word order'))

        strengthener_method = \
            forms.ChoiceField(
                choices=strengthener_method_choices,
                label=_('Method of strengthening a word after pressing YES'))

    return WDictForm

def create_WordPairForm(wdict):

    CF = forms.CharField
    DF = forms.DateField
    IF = forms.IntegerField

    class WordPairForm(forms.Form):
        word_in_lang1 = CF(label=(_('Word in "%(lang)s"') %
                                  {'lang': wdict.lang1}),
                           widget=forms.Textarea(attrs={'rows': 3}))
        word_in_lang2 = CF(label=(_('Word in "%(lang)s"') %
                                  {'lang': wdict.lang2}),
                           widget=forms.Textarea(attrs={'rows': 3}))
        explanation = CF(label=_('Notes'),
                         widget=forms.Textarea,
                         required=False)
        labels = CF(label=_('Labels'),
                    required=False)
        date_added = DF(label=_('Date of addition'))
        date1 = DF(widget=forms.TextInput(attrs={'size': 12}))
        date2 = DF(widget=forms.TextInput(attrs={'size': 12}))
        strength1 = IF(widget=forms.TextInput(attrs={'size': 5}))
        strength2 = IF(widget=forms.TextInput(attrs={'size': 5}))
        display_mode = CF(widget=forms.HiddenInput())

    return WordPairForm


def CreateImportWordPairsForm(wdict):

    class ImportForm(forms.Form):
         text = forms.CharField(widget=forms.Textarea,
                                label=_("Text") + ':')
         labels = forms.CharField(label=_("Labels") + ':',
                                 required=False)

    return ImportForm


def CreateDeleteWDictForm(wdict):
    label = \
        (_('Are you sure that you want to delete dictionary "%(wdict)s"?') %
         {'wdict': wdict.name})
    class DeleteWDictForm(forms.Form):
         sure = forms.BooleanField(label=label, required=False)
    return DeleteWDictForm


##### Decorators #####


def wdict_access_required(f):

    @login_required
    @functools.wraps(f)
    def wrapper(request, wdict_id, *args, **kw):

        # Get the dictionary; if it does not exist or the user does not own it,
        # send him to page 404
        wdict = get_object_or_404(WDict, pk=wdict_id, user=request.user)

        return f(request, wdict, *args, **kw)

    return wrapper


def word_pair_access_required(f):

    @login_required
    @functools.wraps(f)
    def wrapper(request, word_pair_id, *args, **kw):

        # Get the dictionary; if it does not exist or the user does not own it,
        # send him to page 404
        wp = get_object_or_404(WordPair,
                              pk=word_pair_id,
                               wdict__user=request.user)
        wdict = wp.wdict
        return f(request, wp, wdict, *args, **kw)

    return wrapper


def set_lang(f):

    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        set_lang_fun(request)
        return f(request, *args, **kw)

    return wrapper


##### Index view #####

def get_elevator_speech(request):
    help_basics_url = reverse('ew.views.help', args=[request.LANGUAGE_CODE])
    text = (_('ExponWords is a web application for <strong>learning '
              'words</strong>. It helps learn the word pairs fed by the user '
              'using the principle that <strong>the more we have already '
              'practiced a word, the less we need to practice it '
              'in the future</strong>. '
              'You can read more '
              '<a href="%(help_basics_url)s#basics">here</a>.') %
            {'help_basics_url': help_basics_url})
    return text

def get_footnote(request):
    site = get_current_site(request).domain
    text = (_('%(site)s is a free service. ExponWords is open '
              'source software distributed under the %(lic_pre)sApache '
              'License version 2%(lic_post)s. The source code repository '
              'can be found %(ewrepo_pre)shere%(ewrepo_post)s.') %
            {'lic_pre':
                '<a href="http://www.apache.org/licenses/LICENSE-2.0.txt">',
             'lic_post': '</a>',
             'ewrepo_pre': '<a href="https://github.com/hcs42/ExponWords">',
             'ewrepo_post': '</a>',
             'site': site})
    return text

def index(request):
    user = request.user
    if user.is_authenticated():
        set_lang_fun(request)
        username = user.username
        wdicts = WDict.objects.filter(user=user, deleted=False)
        wdicts_augm = sorted([(normalize_string(wdict.name),
                              wdict,
                              len(wdict.get_words_to_practice_today()))
                              for wdict in wdicts])
    else:
        username = None
        wdicts_augm = None

    elevator_speech = get_elevator_speech(request)
    footnote = get_footnote(request)

    models.log(request, 'index')
    return render(
               request,
               'ew/index.html',
               {'wdicts_augm': wdicts_augm,
                'username': username,
                'elevator_speech': elevator_speech,
                'footnote': footnote})


##### Views when logged out #####


def send_registration_email(request, username, email_address, lang):

    site = get_current_site(request)
    subject = (_('Welcome to %(site_name)s') %
               {'site_name': site.name})

    template = loader.get_template('ew/registration/registration_email.html')
    context = {'username': username,
               'site_name': site.name,
               'site_domain': site.domain}
    body = template.render(Context(context))

    models.log(request,
               'registration_email_sending',
               'to %s in language %s' % (email_address, lang))
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
              [email_address], fail_silently=False)
    models.log(request,
               'registration_email_sent',
               'to %s in language %s' % (email_address, lang))


def create_user(request, username, password1, password2, email_address,
                captcha, lang, release_emails):

    if captcha.strip() != '6':
        raise models.EWException(_('Some fields are invalid.'))
    elif password1 != password2:
        raise models.EWException(_('The two passwords do not match.'))
    elif len(password1) < 6:
        raise models.EWException(_('The password has to be at least 6 '
                                   'characters long!'))
    else:

        try:
            user = User.objects.create_user(username, email_address, password1)
        except django.db.IntegrityError:
            raise models.EWException(_('This username is already used.'))

        user.save()
        ewuser = models.get_ewuser(user)
        ewuser.lang = lang
        ewuser.release_emails = release_emails
        ewuser.save()
        send_registration_email(request, username, email_address, lang)
        messages.success(request, _('Successful registration. Please log in!'))
        index_url = reverse('ew.views.index', args=[])
        return HttpResponseRedirect(index_url)


def register(request):

    release_emails_label = \
        unicode(_('Send me emails when ExponWords has new features')) + ' ' + \
        unicode(_('(about once a month; can be turned off at any time from '
                  'Settings)'))

    class RegisterForm(forms.Form):
        username = forms.CharField(max_length=255,
                                   label=_('Username'))
        password1 = forms.CharField(max_length=255,
                                    widget=forms.PasswordInput,
                                    label=_('Password'))
        password2 = forms.CharField(max_length=255,
                                    widget=forms.PasswordInput,
                                    label=_('Password again'))
        email = forms.CharField(max_length=255,
                                        label=_('Email address'))
        c = forms.CharField(max_length=255,
                            label='3 + 3 =')
        release_emails = forms.BooleanField(label=release_emails_label,
                                            required=False)


    if request.method == 'POST':
        models.log(request, 'register')
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            email_address = form.cleaned_data['email']
            captcha = form.cleaned_data['c']
            release_emails = form.cleaned_data['release_emails']
            lang = django.utils.translation.get_language()
            try:
                return create_user(request, username, password1, password2,
                                   email_address, captcha, lang,
                                   release_emails)
            except models.EWException, e:
                messages.error(request, _(e.value))
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = RegisterForm(initial={'release_emails': True})

    else:
        assert(False)

    return render(
               request,
               'ew/register.html',
               {'form':  form})


def language(request):
    return render(
               request,
               'ew/lang.html',
               {})


def help(request, lang):
    models.log(request, 'help')
    langs = [langcode for langcode, langname in settings.LANGUAGES]
    if lang in langs:
        return render(
                   request,
                   'ew/help/help-%s.html' % lang,
                   {'version': models.version})
    else:
        raise Http404


def docs(request, lang, page):
    models.log(request, page)
    filename = '%s-%s.html' % (page, lang)
    filepath = os.path.join(settings.PROJECT_DIR, 'ew', 'templates', 'ew',
                            'help', filename)
    if os.path.exists(filepath):
        return render(
                   request,
                   'ew/help/' + filename,
                   {'version': models.version})
    else:
        raise Http404


##### Views when logged in #####


@wdict_access_required
@set_lang
def wdict(request, wdict):
    words_count = len(wdict.wordpair_set.filter(deleted=False))
    todays_words_count = len(wdict.get_words_to_practice_today())
    beta_user = (request.user.username == 'hcs')
    return render(request,
                  'ew/wdict.html',
                  {'wdict': wdict,
                   'words_count': words_count,
                   'beta_user': beta_user,
                   'todays_words_count': todays_words_count})


def get_default_wp_data(user):
    return {'date_added': models.get_today(user),
            'date1': models.get_today(user),
            'date2': models.get_today(user),
            'strength1': 0,
            'strength2': 0}


def copy_cleaned_fields(form, wp, fields):
    for key in fields:
        setattr(wp, key, form.cleaned_data[key])

def set_word_pair_from_form(wp, form, user, display_mode):

    copy_cleaned_fields(form, wp, WordPair.get_simple_fields())

    if display_mode == 'advanced':
        copy_cleaned_fields(form, wp, WordPair.get_advanced_fields())
    else:
        for key, value in get_default_wp_data(user).items():
            setattr(wp, key, value)

def get_styles(display_mode):
    if display_mode == 'simple':
        return '', 'display: none;'
    elif display_mode == 'advanced':
        return 'display: none;', ''

def create_duplicate_msg(duplicate_word_pairs, text_singular, text_plural):
    if len(duplicate_word_pairs) == 0:
        return ''

    message = []
    text = unicode(text_singular if len(duplicate_word_pairs) == 1
                                 else text_plural)

    message += ['<div>\n',
                text, ':\n',
                '<ul>\n']
    for wp2 in duplicate_word_pairs:
        wp2_url = reverse('ew.views.edit_word_pair', args=[wp2.id])
        message += ['<li>\n',
                    '<a href="', wp2_url, '">',
                    unicode(wp2.get_short_repr()), '</a>\n',
                    '</li>\n']
    message += ['</ul>\n',
                '</div>\n']
    return ''.join(message)

@wdict_access_required
@set_lang
def add_word_pair(request, wdict):

    WordPairForm = create_WordPairForm(wdict)
    message = ''
    if request.method == 'POST':

        # saving the display mode to the session
        display_mode = request.POST.get('display_mode', 'simple')
        request.session['ew_wp_display_mode'] = display_mode

        models.log(request, 'add_word_pair')

        form = WordPairForm(request.POST)
        if form.is_valid():

            # creating the new word pair
            wp = WordPair()
            set_word_pair_from_form(wp, form, request.user, display_mode)
            wdict.wordpair_set.add(wp)
            wp.save()
            wdict.save()

            # saving some fields to the session
            request.session['ew_add_wp_fields'] = \
                (wp.get_saved_fields(), datetime.datetime.now())

            # redirection
            wdict_url = reverse('ew.views.add_word_pair', args=[wdict.id])
            return HttpResponseRedirect(wdict_url + '?wp=' + str(wp.id))
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        wpid = request.GET.get('wp')
        if wpid is not None:
            wp_url = reverse('ew.views.edit_word_pair', args=[wpid])
            message = [unicode(_('Word pair added')),
                       ': <a href="' + wp_url + '">',
                        unicode(_('edit')) + '</a>\n']

            # Create text about duplicates
            wp = get_object_or_404(WordPair,
                                   pk=wpid,
                                   wdict__user=request.user)
            same_word_pairs, similar_word_pairs = wp.wdict.get_duplicates(wp)
            message.append(create_duplicate_msg(
                               same_word_pairs,
                                _('The following word pair is the same'),
                                _('The following word pairs are the same')))
            message.append(create_duplicate_msg(
                               similar_word_pairs,
                                _('The following word pair is similar'),
                                _('The following word pairs are similar')))

            message = ''.join(message)

        data = get_default_wp_data(request.user)

        # Load the saved fields if they were saved not longer than 1 hour ago
        ew_add_wp_fields = request.session.get('ew_add_wp_fields')
        if ew_add_wp_fields is not None:
            saved_field, save_time = ew_add_wp_fields
            if (datetime.datetime.now() - save_time <
                datetime.timedelta(seconds=
                                   ADD_WORD_PAIR_DATE_REMEMBER_SECONDS)):
                for field, value in saved_field.items():
                    data[field] = value

        display_mode = request.session.get('ew_wp_display_mode', 'simple')
        data['display_mode'] = display_mode

        form = WordPairForm(initial=data)
    else:
        assert(False)

    simple_style, advanced_style = get_styles(display_mode)

    return render(
               request,
               'ew/add_word_pair.html',
               {'form':  form,
                'message': message,
                'wdict': wdict,
                'lang1': wdict.lang1,
                'lang2': wdict.lang2,
                'simple_style': simple_style,
                'advanced_style': advanced_style})


def import_word_pairs(request, wdict, import_fun, page_title, help_text,
                      source):

    ImportForm = CreateImportWordPairsForm(wdict)
    if request.method == 'POST':
        models.log(request, 'import_word_pairs', source)
        form = ImportForm(request.POST)
        if form.is_valid():
            try:
                word_pairs = import_fun(form.cleaned_data['text'], wdict)
                labels = form.cleaned_data['labels']
                for wp in word_pairs:
                    wp.add_labels(labels)
                    wp.save()
                messages.success(request, _('Word pairs added.'))
            except Exception, e:
                messages.error(request, _('Error: ') + unicode(e))
            else:
                import_url = reverse('ew.views.' + source, args=[wdict.id])
                return HttpResponseRedirect(import_url)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = ImportForm()

    else:
        assert(False)

    return render(
               request,
               'ew/import_word_pairs.html',
               {'form':  form,
                'help_text': help_text,
                'wdict': wdict,
                'page_title': page_title})


@wdict_access_required
@set_lang
def import_word_pairs_from_text(request, wdict):

    page_title = _('Import word pairs from text')
    help_text = ""
    return import_word_pairs(request, wdict, models.import_textfile,
                             page_title, help_text,
                             'import_word_pairs_from_text')


@wdict_access_required
@set_lang
def export_word_pairs_to_text(request, wdict):
    models.log(request, 'export_word_pairs_to_text')
    text = models.export_textfile(wdict)
    return render(
               request,
               'ew/export_wdict_as_text.html',
               {'wdict': wdict,
                'text': text})


@wdict_access_required
@set_lang
def import_word_pairs_from_tsv(request, wdict):

    page_title = _('Import word pairs from tab-separated values')
    help_text = _("Write one word per line. Each word should contain two or "
                "three fields: word in the first language; word in the "
                "second language; notes. The last one is optional. "
                "The fields should be separated by a TAB character. If a "
                "spreadsheet is opened in as spreadsheet editor application "
                "(such as LibreOffice, OpenOffice.org or Microsoft Excel), "
                "and it contains these three columns, which are copied and "
                "pasted here, then it will have exactly this format.")
    return import_word_pairs(request, wdict, models.import_tsv,
                             page_title, help_text,
                             'import_word_pairs_from_tsv')


@wdict_access_required
@set_lang
def modify_wdict(request, wdict):

    WDictForm = create_WDictForm()
    if request.method == 'POST':
        models.log(request, 'modify_wdict')
        form = WDictForm(request.POST)
        if form.is_valid():
            for field in ('name', 'lang1', 'lang2', 'practice_word_order',
                          'strengthener_method'):
                setattr(wdict, field, form.cleaned_data[field])
            wdict.save()
            messages.success(request, _('Dictionary modified.'))
            wdict_url = reverse('ew.views.wdict', args=[wdict.id])
            return HttpResponseRedirect(wdict_url)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = WDictForm({'name': wdict.name,
                          'lang1': wdict.lang1,
                          'lang2': wdict.lang2,
                          'practice_word_order': wdict.practice_word_order,
                          'strengthener_method': wdict.strengthener_method})

    else:
        assert(False)

    return render(
               request,
               'ew/modify_wdict.html',
               {'form': form,
                'wdict': wdict})


@wdict_access_required
@set_lang
def delete_wdict(request, wdict):

    DeleteWDictForm = CreateDeleteWDictForm(wdict)
    if request.method == 'POST':
        models.log(request, 'delete_wdict')
        form = DeleteWDictForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['sure']:
                wdict.deleted = True
                wdict.save()
                messages.success(request, _('Dictionary deleted.'))
                index_url = reverse('ew.views.index', args=[])
                return HttpResponseRedirect(index_url)
            else:
                messages.error(
                    request,
                    _('Please check in the "Are you sure" checkbox if '
                      'you really want to delete the dictionary.'))
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = DeleteWDictForm()

    else:
        assert(False)

    return render(
               request,
               'ew/delete_wdict.html',
               {'form':  form,
                'wdict': wdict})


@login_required
@set_lang
def add_wdict(request):

    WDictForm = create_WDictForm()
    if request.method == 'POST':
        models.log(request, 'add_wdict')
        form = WDictForm(request.POST)
        if form.is_valid():
            wdict = WDict()
            wdict.user = request.user
            wdict.name = form.cleaned_data['name']
            wdict.lang1 = form.cleaned_data['lang1']
            wdict.lang2 = form.cleaned_data['lang2']
            wdict.practice_word_order = \
                form.cleaned_data['practice_word_order']
            wdict.strengthener_method = \
                form.cleaned_data['strengthener_method']
            wdict.save()
            messages.success(request, _('Dictionary created.'))
            wdict_url = reverse('ew.views.wdict', args=[wdict.id])
            return HttpResponseRedirect(wdict_url)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = WDictForm()

    else:
        assert(False)

    return render(
               request,
               'ew/add_wdict.html',
               {'form':  form})


@login_required
@set_lang
def visualize(request):
    class WDictData(object):
        def __init__(self, name, question_counts):
            object.__init__(self)
            self.name = name
            self.question_counts = question_counts

    dates, wdicts, date_to_question_count = \
        models.calc_future(request.user, 30, models.get_today(request.user))

    sum_data = WDictData(_('Sum'), [0 for date in dates])
    wdicts_data = [sum_data]
    for wdict in wdicts:
        wdict_data = WDictData(wdict.name, [])
        wdicts_data.append(wdict_data)
        for index, date in enumerate(dates):
            question_count = date_to_question_count[(wdict, date)]
            wdict_data.question_counts.append(question_count)
            sum_data.question_counts[index] += question_count

    return render(
               request,
               'ew/visualize.html',
               {'wdicts_data': wdicts_data,
                'dates': [date.isoformat() for date in dates]})


@login_required
@set_lang
def ew_settings(request):

    practice_arrangements_choices = \
        [('normal', _('Normal')),
         ('less_scrolling', _('Less scrolling'))]

    practice_word_order_choices = PRACTICE_WORD_ORDER_CHOICES
    strengthener_method_choices = STRENGTHENER_METHOD_CHOICES

    langs = ([(langcode, langname)
              for langcode, langname in settings.LANGUAGES])

    timezones = [(str(tz_index),
                 'UTC' + ('' if tz_index < 0 else '+') + str(tz_index))
                 for tz_index in range(-11, 13)]

    class SettingsForm(forms.Form):
        lang = forms.ChoiceField(choices=langs,
                                 label=_('Language'))
        timezone = forms.ChoiceField(choices=timezones,
                                     label=_('Time zone'))
        turning_point = forms.CharField(max_length=10,
                                        label=_('Turning point'))
        practice_word_order = \
            forms.ChoiceField(
                choices=practice_word_order_choices,
                label=_('Practice page word order'))
        strengthener_method = \
            forms.ChoiceField(
                choices=strengthener_method_choices,
                label=_('Method of strengthening a word after pressing YES'))
        practice_arrangement = \
            forms.ChoiceField(
                choices=practice_arrangements_choices,
                label=_('Practice page arrangement'))
        button_size = forms.IntegerField(label=_('Button size'))
        question_size = forms.IntegerField(label=_('Question size'))
        answer_size = forms.IntegerField(label=_('Answer size'))
        explanation_size = forms.IntegerField(label=_('Notes size'))
        quick_labels = forms.CharField(label=_('Quick labels'), required=False)
        email_address = forms.CharField(max_length=255,
                                        label=_('Email address'))
        release_emails = \
            forms.BooleanField(
                label=_('Send me emails when ExponWords has new features'),
                required=False)

    if request.method == 'POST':
        models.log(request, 'settings')
        form = SettingsForm(request.POST)
        if form.is_valid():
            c = form.cleaned_data
            lang_code = c['lang']
            if (lang_code and
                (django.utils.translation.check_for_language(lang_code))):
                ewuser = models.get_ewuser(request.user)
                ewuser.lang = lang_code
                ewuser.timezone = c['timezone']
                ewuser.set_turning_point_str(c['turning_point'])
                ewuser.practice_word_order = c['practice_word_order']
                ewuser.strengthener_method = c['strengthener_method']
                ewuser.practice_arrangement = c['practice_arrangement']
                ewuser.button_size = c['button_size']
                ewuser.question_size = c['question_size']
                ewuser.quick_labels = c['quick_labels']
                ewuser.answer_size = c['answer_size']
                ewuser.explanation_size = c['explanation_size']
                request.user.email = c['email_address']
                ewuser.release_emails = c['release_emails']
                request.user.save()
                ewuser.save()
                set_lang_fun(request)
                settings_url = reverse('ew.views.ew_settings', args=[])

                # If the new setting contains 'Use language of the browser',
                # then the language of the browser is not set yet (dispite the
                # set_lang_fun call above), so we can't use the '_' translation
                # function. Therefore we only add the 'ew_settings_saved' key
                # to the session now, and when the settings page is reloaded
                # again after the redirection here, we check for this key and
                # if it exists, we use the '_' function to translate the
                # 'Settings saved.' message.
                request.session['ew_settings_saved'] = True

                return HttpResponseRedirect(settings_url)
            else:
                messages.error(request,
                               _('Invalid language code') + ': ' + lang_code)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        ewuser = models.get_ewuser(request.user)
        form = SettingsForm({
                   'lang': ewuser.lang,
                   'timezone': ewuser.timezone,
                   'turning_point': ewuser.get_turning_point_str(),
                   'practice_arrangement': ewuser.practice_arrangement,
                   'practice_word_order': ewuser.practice_word_order,
                   'strengthener_method': ewuser.strengthener_method,
                   'button_size': ewuser.button_size,
                   'question_size': ewuser.question_size,
                   'answer_size': ewuser.answer_size,
                   'explanation_size': ewuser.explanation_size,
                   'quick_labels': ewuser.quick_labels,
                   'email_address': request.user.email,
                   'release_emails': ewuser.release_emails})

    else:
        assert(False)

    if request.session.pop('ew_settings_saved', False):
        messages.success(request, _('Settings saved.'))

    return render(
               request,
               'ew/settings.html',
               {'form':  form})


##### Practice #####


def escape_for_html(explanation, indent=False):
    """Escapes the given string so that it can be printed as HTML. Optionally
    it indents each line with 4 non-breakable spaces.

    **Argument:**

    - `explanation` (str)

    **Returns:** str
    """

    # Remove the trailing newline
    if (len(explanation) > 1) and (explanation[-1] == '\n'):
        explanation = explanation[:-1]

    # Indentation
    def insert_nbps(matchobject):
        """Returns the same number of "&nbsp;":s as the number of matched
        characters."""
        spaces = matchobject.group(1)
        space_count = len(spaces)
        if indent:
            space_count += 4
        return '&nbsp;' * space_count
    regexp = re.compile(r'^( *)', re.MULTILINE)
    explanation = re.sub('&', '&amp;', explanation)
    explanation = re.sub('<', '&lt;', explanation)
    explanation = re.sub('>', '&gt;', explanation)
    explanation = re.sub(regexp, insert_nbps, explanation)

    return '<br/>'.join(explanation.splitlines())


def words_to_practice_to_json(words_to_practice, limit):
    word_list = []

    if limit:
        words_to_practice_now = words_to_practice[:PRACTICE_WORD_COUNT_LIMIT]
    else:
        words_to_practice_now = words_to_practice

    for wp, direction in words_to_practice_now:

        if wp.explanation:
            expl_labels = wp.explanation
            if wp.labels:
                expl_labels += '\n\n'
        else:
            expl_labels = ''
        if wp.labels:
            expl_labels += '[%s]' % wp.labels

        wdict = wp.wdict
        user = wdict.user

        #if user.username == 'bandris':
        #    dimness_day = models.get_today(user) + datetime.timedelta(days=1)
        #    dimness = wp.get_dimness(direction, dimness_day, silent=True)
        #    expl_labels += '\nDimness: ' + str(dimness)

        if user.username in ('hcs', 'bandris'):
            today = models.get_today(user)
            tomorrow = today + datetime.timedelta(days=1)
            last_query_date, due_date, due_interval_len = \
                wp.get_date_info(direction)
            strength2, date2 = wp.strengthen(direction, dry_run=True)

            expl_labels += ('\nDimness today: ' +
                            str(wp.get_dimness(direction, today,
                                               silent=True)) +
                            '\nDimness tomorrow: ' +
                            str(wp.get_dimness(direction, tomorrow,
                                               silent=True)) +
                            '\nStrength1: ' +
                            str(wp.get_strength(direction)) +
                            '\nLast query date (calculated): ' +
                            str(last_query_date) +
                            '\nDate1 (due date): ' +
                            str(due_date) +
                            '\nLast due interval length (calculated): ' +
                            str(due_interval_len) +
                            '\nStrength2: ' +
                            str(strength2) +
                            '\nDate2: ' +
                            str(date2) +
                            '\nNext due interval length: ' +
                            str((date2 - last_query_date).days))

        word_list.append([escape_for_html(wp.word_in_lang1),
                          escape_for_html(wp.word_in_lang2),
                          direction,
                          wp.id,
                          wp.get_date(direction).isoformat(),
                          wp.get_strength(direction),
                          escape_for_html(expl_labels, indent=True)])

    return json.dumps({'all_words_to_practice': len(words_to_practice),
                       'word_list': word_list})


@wdict_access_required
@set_lang
def practice_wdict(request, wdict):
    text = 'dict: "%s"' % wdict.name
    models.log(request, 'practice_wdict', text)
    ewuser = models.get_ewuser(request.user)
    return render(request,
                  'ew/practice_wdict.html',
                  {'wdict': wdict,
                   'words_to_practice': '"normal"',
                   'ewuser': ewuser,
                   'user': request.user,
                   'quick_labels': ewuser.get_quick_labels()})


@wdict_access_required
@set_lang
def practice_wdict_early(request, wdict):
    text = 'dict: "%s"' % wdict.name
    models.log(request, 'practice_wdict_early', text)
    ewuser = models.get_ewuser(request.user)
    return render(request,
                  'ew/practice_wdict.html',
                  {'wdict': wdict,
                   'words_to_practice': '"early"',
                   'ewuser': ewuser,
                   'user': request.user,
                   'quick_labels': ewuser.get_quick_labels()})


@login_required
@set_lang
def practice(request):
    models.log(request, 'practice')
    words_to_practice = request.session['ew_words_to_practice']
    json_str = words_to_practice_to_json(words_to_practice, limit=False)
    ewuser = models.get_ewuser(request.user)
    return render(request,
                  'ew/practice_wdict.html',
                  {'wdict': None,
                   'words_to_practice': json_str,
                   'ewuser': ewuser,
                   'quick_labels': ewuser.get_quick_labels()})


@wdict_access_required
def get_words_to_practice_today(request, wdict):

    try:

        if request.method != 'GET':
            raise Http404
        word_list_type = request.GET['word_list_type']

        words_to_practice = \
            wdict.get_words_to_practice_today(word_list_type=word_list_type)
        wdict.sort_words(words_to_practice, word_list_type=word_list_type)
        json_str = words_to_practice_to_json(words_to_practice, limit=True)
        return HttpResponse(json_str,
                            mimetype='application/json')
    except Exception, e:
        traceback.print_stack()
        exc_info = sys.exc_info()
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2])
        raise exc_info[0], exc_info[1], exc_info[2]


@login_required
def update_word(request):
    try:

        answer = json.loads(request.POST['answer'])
        word_pair_id = json.loads(request.POST['word_index'])
        direction = json.loads(request.POST['direction'])
        old_date = json.loads(request.POST['old_date'])
        old_strength = json.loads(request.POST['old_strength'])

        wp = get_object_or_404(WordPair,
                               pk=word_pair_id,
                               wdict__user=request.user)

        if (old_date != wp.get_date(direction).isoformat() or
            old_strength != wp.get_strength(direction)):

            # This update have already been performed or another process
            # modified the word's date and/or strength; in either case,
            # we don't want to modify the word.
            return HttpResponse(json.dumps('ok'),
                                mimetype='application/json')

        assert(isinstance(answer, bool))
        if answer:
            # The user knew the answer
            wp.strengthen(direction)
        else:
            # The user did not know the answer
            wp.weaken(direction)
        wp.save()

        return HttpResponse(json.dumps('ok'),
                             mimetype='application/json')
    except Exception, e:
        traceback.print_stack()
        exc_info = sys.exc_info()
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2])
        raise exc_info[0], exc_info[1], exc_info[2]


@login_required
def add_label(request):
    try:

        word_pair_id = json.loads(request.POST['word_index'])
        label = json.loads(request.POST['label'])

        wp = get_object_or_404(WordPair,
                               pk=word_pair_id,
                               wdict__user=request.user)

        wp.add_labels(label)
        wp.save()

        return HttpResponse(json.dumps('ok'),
                             mimetype='application/json')
    except Exception, e:
        traceback.print_stack()
        exc_info = sys.exc_info()
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2])
        raise exc_info[0], exc_info[1], exc_info[2]


##### Search and operations #####


def parse_query_label(query_label_raw):
    if query_label_raw in ('', 'all'):
        return None
    else:
        return query_label_raw


def search_in_db(user, query_wdict, query_label, query_text):
    if query_wdict in ('', 'all'):
        all_word_pairs = WordPair.objects.filter(wdict__user=user,
                                                 wdict__deleted=False,
                                                 deleted=False)
    else:
        wdict_id = int(query_wdict)
        wdict = get_object_or_404(WDict, pk=wdict_id, user=user)
        all_word_pairs = WordPair.objects.filter(wdict=wdict,
                                                 deleted=False)
    word_pairs = []
    query_words = [normalize_string(query_word)
                   for query_word in query_text.split()]
    query_items = []
    for query_word in query_words:
        if query_word.startswith('label:'):
            query_items.append(('label', query_word[6:]))
        else:
            query_items.append(('text', query_word))

    for wp in all_word_pairs:
        wp_matches_all = True
        if ((query_label is not None) and
            (query_label not in wp.get_label_set())):
            # We require a certain label but wp does not have it
            continue

        for query_item_type, query_item_value in query_items:
            query_item_matches = False
            if query_item_type == 'label':
                labels = normalize_string(unicode(wp.labels))
                query_item_matches = (labels.find(query_item_value) != -1)
            else: # query_item_type == 'text'
                for field in models.WordPair.get_fields_to_be_edited():
                    field_text = normalize_string(unicode(getattr(wp, field)))
                    if (field_text.find(query_item_value) != -1):
                        query_item_matches = True
                        break
            if not query_item_matches:
                wp_matches_all = False
                break
        if wp_matches_all:
            word_pairs.append(wp)
    return word_pairs


@login_required
@set_lang
def search(request):

    wdicts = WDict.objects.filter(user=request.user, deleted=False)
    wdict_choices = [(wdict.id, wdict.name) for wdict in wdicts]
    wdict_choices_full = [('all', _('All'))] + wdict_choices

    labels = sorted(models.get_labels(request.user))
    label_choices_full = ([('all', _('All'))] +
                          [(label, label) for label in labels])

    hits_per_page_choices = [(str(i), str(i)) for i in (10, 20, 50, 100, 1000)]

    class SearchForm(forms.Form):
        q = forms.CharField(max_length=255,
                            label=_('Search expression') + ':',
                            required=False)
        dict = forms.ChoiceField(choices=wdict_choices_full,
                                 label=_('Dictionary') + ':',
                                 required=False)
        label = LenientChoiceField(choices=label_choices_full,
                                   label=_('Label') + ':',
                                   required=False)
        hits_per_page = LenientChoiceField(choices=hits_per_page_choices,
                                           label=_('Hits per page') + ':',
                                           required=False)
        show_hits = forms.BooleanField(label=_('Show hits') + ':',
                                       required=False)

    if request.method != 'GET':
        raise Http404

    form = SearchForm(request.GET)
    if not form.is_valid():
        raise Http404

    query_text = form.cleaned_data['q']
    query_wdict = form.cleaned_data['dict']
    query_label = parse_query_label(form.cleaned_data['label'])
    hits_per_page_raw = form.cleaned_data['hits_per_page']
    show_hits = form.cleaned_data['show_hits']

    if not hits_per_page_raw:
        hits_per_page = 10
    else:
        hits_per_page = int(hits_per_page_raw)

    source_url = request.get_full_path()
    pagination_url = remove_query_param(request.get_full_path(), 'page')

    # If we don't have a 'q' parameter, we will show the basic search page. If
    # we do have one, we will perform the search, even if it is empty.

    if query_wdict in ('', 'all'):
        wdict = None
    else:
        wdict = get_object_or_404(WDict, pk=int(query_wdict),
                                  user=request.user)

    if 'q' not in request.GET:
        if wdict is None:
            form = SearchForm({'show_hits': True})
        else:
            form = SearchForm({'dict': query_wdict, 'show_hits': True})

        return render(request,
                      'ew/search.html',
                      {'form': form,
                       'wdict': wdict,
                       'source_url': source_url,
                       'result_exists': False,
                       'show_hits': False,
                       'wdict_choices': wdict_choices})

    else:
        word_pairs = \
            search_in_db(request.user, query_wdict, query_label, query_text)

        paginator = Paginator(word_pairs, hits_per_page)
        page = request.GET.get('page', 1)

        try:
            pagination_info = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            pagination_info = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of
            # results.
            pagination_info = paginator.page(paginator.num_pages)

        current_page_index = \
            (_('Page %(current_page_index)s of %(page_count)s') %
             {'current_page_index': pagination_info.number,
              'page_count': pagination_info.paginator.num_pages})

        if show_hits:
            word_pairs_and_exps = \
                [(wp,
                  escape_for_html(wp.word_in_lang1),
                  escape_for_html(wp.word_in_lang2),
                  escape_for_html(wp.explanation, indent=True))
                 for wp in pagination_info.object_list]
        else:
            word_pairs_and_exps = []

        context = {'form': form,
                   'wdict': wdict,
                   'source_url': source_url,
                   'wdict_choices': wdict_choices,
                   'show_hits': show_hits,
                   'hits_count': len(word_pairs),
                   'result_exists': True,
                   'pagination_url': pagination_url,
                   'pagination_info': pagination_info,
                   'current_page_index': current_page_index,
                   'word_pairs_and_exps': word_pairs_and_exps}

        if wdict is not None:
            context.update({'lang1': wdict.lang1,
                            'lang2': wdict.lang2})

        return render(request, 'ew/search.html', context)


@word_pair_access_required
@set_lang
def edit_word_pair(request, wp, wdict):

    WordPairForm = create_WordPairForm(wdict)
    if request.method == 'POST':

        # saving the display mode to the session
        display_mode = request.POST.get('display_mode', 'simple')
        request.session['ew_wp_display_mode'] = display_mode

        models.log(request, 'edit_word_pair')

        if 'delete_word_pair' in request.POST:
            wp.deleted = True
            wp.save()
            messages.success(request, _('Word pair deleted.'))
            wdict_url = reverse('ew.views.index', args=[])
            return HttpResponseRedirect(wdict_url)

        form = WordPairForm(request.POST)
        if form.is_valid():

            if display_mode == 'simple':
                fields_to_copy = WordPair.get_simple_fields()
            else:
                fields_to_copy = WordPair.get_fields_to_be_edited()

            copy_cleaned_fields(form, wp, fields_to_copy)
            wp.save()
            messages.success(request, _('Word pair modified.'))
            wdict_url = reverse('ew.views.edit_word_pair', args=[wp.id])
            return HttpResponseRedirect(wdict_url)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        data = {}
        for field in WordPair.get_fields_to_be_edited():
            data[field] = getattr(wp, field)

        display_mode = request.session.get('ew_wp_display_mode', 'simple')
        data['display_mode'] = display_mode

        form = WordPairForm(data=data)

    else:
        assert(False)

    simple_style, advanced_style = get_styles(display_mode)

    return render(
               request,
               'ew/edit_word_pair.html',
               {'form': form,
                'word_pair': wp,
                'wdict': wdict,
                'lang1': wdict.lang1,
                'lang2': wdict.lang2,
                'simple_style': simple_style,
                'advanced_style': advanced_style})


def get_word_pairs_to_use(request):

    # Deciding whether:
    # - to use an explicit list of word pair ids (if show_hits is true); or
    # - to rerun the query (if show_hits is false)

    source_url = request.POST.get('source_url')
    if source_url:
        url_list = list(urlparse.urlparse(source_url))
        query_list = urlparse.parse_qsl(url_list[4], keep_blank_values=True)
        query_dict = dict(query_list)
        show_hits = ('show_hits' in query_dict)
    else:
        show_hits = True

    # Calculating the list of word pairs

    if show_hits:
        word_pairs = WordPair.objects.filter(wdict__user=request.user,
                                             wdict__deleted=False,
                                             deleted=False)
        word_pairs_to_use = []
        for wp in word_pairs:
            if unicode(wp.id) in request.POST:
                word_pairs_to_use.append(wp)
        return word_pairs_to_use

    else:
        query_text = query_dict['q']
        query_wdict = query_dict['dict']
        query_label = parse_query_label(query_dict['label'])

        word_pairs = \
            search_in_db(request.user, query_wdict, query_label, query_text)
        return word_pairs


@login_required
def operation_on_word_pairs(request):

    models.log(request, 'operation_on_word_pairs')

    # Select the word pairs to use (i.e. to do the operation with)
    word_pairs_to_use = get_word_pairs_to_use(request)

    # Perform the operation

    error_msg = None
    operation = request.POST.get('operation')
    do_operation = False
    if operation == 'delete':
        do_operation = True
    elif operation == 'move':
        target_wdict_id = int(request.POST.get('move_word_pairs_wdict'))
        target_wdict = get_object_or_404(WDict, pk=target_wdict_id,
                                         user=request.user)
        do_operation = True
    elif operation in ('add_labels', 'remove_labels', 'set_labels'):
        labels = request.POST.get(operation + '-labels')
        do_operation = True
    elif operation == 'set_dates_strengths':
        values = {}
        fields = ('date1', 'date2', 'strength1', 'strength2')
        for field in fields:
            raw_value = request.POST.get(field, '').strip()
            if raw_value == '':
                value = None
            elif field.startswith('date'):
                try:
                    value = models.parse_date(raw_value)
                except ValueError:
                    error_msg = (_('Incorrect date: %(date)s. Please use the '
                                   'following format: YYYY-MM-DD.') %
                                 {'date': raw_value})
                    break
            elif field.startswith('strength'):
                try:
                    value = int(raw_value)
                except ValueError:
                    error_msg = (_('Incorrect strength: %(strength)s. Please '
                                   'specify it as an integer.') %
                                 {'strength': raw_value})
                    break
            else:
                assert(False)
            values[field] = value
        if not error_msg:
            do_operation = True
    elif operation == 'shift_days':
        try:
            days = datetime.timedelta(days=int(request.POST.get('days')))
            do_operation = True
        except ValueError:
            error_msg = _('Please specify the number of days!')
    elif operation == 'practice':
        # We don't do an operation to the words themselves
        practice_scope = request.POST.get('practice_scope')
        do_operation = False
    elif operation == 'export':
        text = models.export_textfile(word_pairs=word_pairs_to_use)
        return render(
                   request,
                   'ew/export_word_pairs_as_text.html',
                   {'text': text})
    else:
        error_msg = _('Operation not recognized') + ': ' + str(operation)

    if do_operation:
        for wp in word_pairs_to_use:
            if operation == 'delete':
                wp.deleted = True
            elif operation == 'move':
                wp.wdict = target_wdict
            elif operation == 'add_labels':
                wp.add_labels(labels)
            elif operation == 'remove_labels':
                wp.remove_labels(labels)
            elif operation == 'set_labels':
                wp.set_labels(labels)
            elif operation == 'set_dates_strengths':
                for field in fields:
                    if values[field] is not None:
                        setattr(wp, field, values[field])
            elif operation == 'shift_days':
                if datetime.date.max - wp.date1 > days:
                    wp.date1 += days
                if datetime.date.max - wp.date2 > days:
                    wp.date2 += days
            wp.save()

    # Redirect the user to the search page where which he issue the operation

    source_url = request.POST.get('source_url')

    if operation == 'practice':
        today = models.get_today(request.user)
        words_to_practice = []
        user_time = models.get_user_time(request.user)
        for wp in word_pairs_to_use:
            if (practice_scope == 'all' or
                models.is_word_due(wp.date1, user_time)):
                words_to_practice.append((wp, 1))
            if (practice_scope == 'all' or
                models.is_word_due(wp.date2, user_time)):
                words_to_practice.append((wp, 2))
        random.shuffle(words_to_practice)

        request.session['ew_words_to_practice'] = words_to_practice
        redirect_url = reverse('ew.views.practice', args=[])

    elif source_url:
        if error_msg is None:
            word_count = len(word_pairs_to_use)
            if word_count == 0:
                message = _('No word pair modified.')
            elif word_count == 1:
                message = _('1 word pair modified.')
            else:
                message = (_('%(count)s word pairs modified.') %
                           {'count': word_count})
            messages.success(request, message)
        else:
            messages.error(request, error_msg)

        redirect_url = source_url

    else:
        redirect_url = reverse('ew.views.index', args=[])

    return HttpResponseRedirect(redirect_url)


##### Staff views #####


def get_announcement_receivers():
    """Returns the users (with their email addresses) who should receive
    notifications about new releases.

    Returns: {lang: [(username, email)]}
    """

    lang_users = {}
    for user in models.EWUser.get_email_receiver_users():
        lang = models.get_ewuser(user).lang
        lang_users.setdefault(lang, []).append((user.username, user.email))
    return lang_users


def send_announcement(request):
    """Sends release announcements in email."""

    for lang, users in get_announcement_receivers().items():

        # The first line of the stored announcement text will be the subject;
        # the rest will be the body.
        ann = models.Announcement.objects.get(lang=lang)
        lines = ann.text.splitlines()
        subject = lines[0]
        body = '\n'.join(lines[1:])

        for username, email in users:
            models.log(request,
                       'announcement_sending',
                       'to %s in language %s' % (email, lang))
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                      [email], fail_silently=False)
            models.log(request,
                       'announcement_sent',
                       'to %s in language %s' % (email, lang))

    messages.success(request, _('Announcement emails sent.'))


@staff_member_required
@set_lang
def announce_release(request):

    # Creating a form based on the supported languages.
    #
    # If it were a normally created class, it would look like this:
    #
    # class AnnounceReleaseForm(forms.Form):
    #     text_en = forms.CharField(widget=forms.Textarea,
    #                               label="en (English)")
    #     text_hu = forms.CharField(widget=forms.Textarea,
    #                               label="hu (Magyar)")
    #     ...maybe other languages in the future
    fields = \
        dict([('text_' + langcode,
                forms.CharField(widget=forms.Textarea,
                                label=('%s (%s)' % (langcode, langname))))
              for langcode, langname in settings.LANGUAGES])
    AnnounceReleaseForm = \
        type('AnnounceReleaseForm', (forms.Form,), fields)

    message = ''
    if request.method == 'POST':
        models.log(request, 'announce_release')

        action = None
        if request.POST.get('save-button'):
            action = 'save'
        elif request.POST.get('announce-button'):
            action = 'announce'
        assert(action is not None)

        form = AnnounceReleaseForm(request.POST)
        if form.is_valid():

            # Saving the text of the announcements
            Ann = models.Announcement
            for langcode, langname in settings.LANGUAGES:
                try:
                    ann = Ann.objects.get(lang=langcode)
                except models.Announcement.DoesNotExist:
                    ann = Ann.objects.create(lang=langcode)
                ann.text = form.cleaned_data['text_' + langcode]
                ann.save()

            messages.success(request, _('Announcement texts saved.'))

            # Sending the announcement emails if needed
            if action == 'announce':
                send_announcement(request)

            url = reverse('ew.views.announce_release', args=[])
            return HttpResponseRedirect(url)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':

        data = {}

        # Read the saved announcements from the database and put them into
        # `data`
        for langcode, langname in settings.LANGUAGES:
            try:
                announcement = models.Announcement.objects.get(lang=langcode)
                data['text_' + langcode] = announcement.text
            except models.Announcement.DoesNotExist:
                pass

        form = AnnounceReleaseForm(initial=data)

    else:
        assert(False)

    return render(
               request,
               'ew/announce_release.html',
               {'form':  form,
                'message': message,
                'lang_users': get_announcement_receivers()})
