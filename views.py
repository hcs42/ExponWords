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

import datetime
import functools
import json
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
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponseServerError, HttpResponseBadRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
import django.db
import django.utils.translation

from ExponWords.ew.models import WordPair, WDict
import ExponWords.ew.models as models


##### Constants #####

ADD_WORD_PAIR_DATE_REMEMBER_SECONDS = 3600 # 1 hour


##### General helper functions #####


def set_lang_fun(request):
    lang = models.get_ewuser(request.user).lang
    request.session['django_language'] = lang
    django.utils.translation.activate(lang)


def set_word_pair_form_labels(wdict, form):
    f = form.fields
    f['word_in_lang1'].label = \
        (_('Word in "%(lang)s"') % {'lang': wdict.lang1}) + ':'
    f['word_in_lang2'].label = \
        (_('Word in "%(lang)s"') % {'lang': wdict.lang2}) + ':'
    f['date_added'].label = \
        _('Date of addition') + ':'
    f['explanation'].label = \
        _('Explanation') + ':'
    f['labels'].label = \
        _('Labels') + ':'
    f['date1'].label = \
        _('Date of next practice from "%(lang)s"') % {'lang': wdict.lang1} + ':'
    f['date2'].label = \
        _('Date of next practice from "%(lang)s"') % {'lang': wdict.lang2} + ':'
    f['strength1'].label = \
        _('Strengh of word from "%(lang)s"') % {'lang': wdict.lang1} + ':'
    f['strength2'].label = \
        _('Strengh of word from "%(lang)s"') % {'lang': wdict.lang2} + ':'


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
    class WDictForm(forms.Form):
        name = forms.CharField(max_length=255,
                               label=_("Name of the dictionary") + ':')
        lang1 = forms.CharField(max_length=255,
                                label=_("Language 1") + ':')
        lang2 = forms.CharField(max_length=255,
                                label=_("Language 2") + ':')
    return WDictForm


class WordPairForm(forms.ModelForm):
    class Meta:
        model = WordPair
        fields = models.WordPair.get_fields_to_be_edited()
        widgets = {
            'word_in_lang1': forms.Textarea(attrs={'rows': 3}),
            'word_in_lang2': forms.Textarea(attrs={'rows': 3})
        }

def CreateImportWordPairsForm(wdict):

    class ImportForm(forms.Form):
         text = forms.CharField(widget=forms.Textarea,
                                label=_("Text") + ':')
         labels = forms.CharField(label=_("Labels") + ':',
                                 required=False)

    return ImportForm


def CreateDeleteWDictForm(wdict):
    label = (_('Are you sure that you want to delete dictionary "%(wdict)s"?') %
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
    website = 'exponwords.com'
    text = (_('%(site)s is a free service. ExponWords is open '
              'source software distributed under the %(gpl_pre)sGNU '
              'Generic Public Licence version 3%(gpl_post)s. The source '
              'code repository can be found '
              '%(ewrepo_pre)shere%(ewrepo_post)s.') %
            {'gpl_pre': '<a href="http://www.gnu.org/licenses/gpl-3.0.html">',
             'gpl_post': '</a>',
             'ewrepo_pre': '<a href="https://github.com/hcs42/ExponWords">',
             'ewrepo_post': '</a>',
             'site': website})
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


def create_user(request, username, password1, password2, email_address,
                captcha, lang):

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
        ewuser.save()
        messages.success(request, _('Successful registration. Please log in!'))
        index_url = reverse('ew.views.index', args=[])
        return HttpResponseRedirect(index_url)


def register(request):

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

    if request.method == 'POST':
        models.log(request, 'register')
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            email_address = form.cleaned_data['email']
            captcha = form.cleaned_data['c']
            lang = django.utils.translation.get_language()
            try:
                return create_user(request, username, password1, password2,
                                   email_address, captcha, lang)
            except models.EWException, e:
                messages.error(request, _(e.value))
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = RegisterForm()

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
                   'ew/help/%s.html' % lang,
                   {'version': models.version})
    else:
        raise Http404


##### Views when logged in #####


@wdict_access_required
@set_lang
def wdict(request, wdict):
    words_count = len(wdict.wordpair_set.filter(deleted=False))
    todays_words_count = len(wdict.get_words_to_practice_today())
    return render(request,
                  'ew/wdict.html',
                  {'wdict': wdict,
                   'words_count': words_count,
                   'todays_words_count': todays_words_count})


@wdict_access_required
@set_lang
def add_word_pair(request, wdict):

    message = ''
    if request.method == 'POST':
        models.log(request, 'add_word_pair')
        form = WordPairForm(request.POST)
        if form.is_valid():

            # creating the new word pair
            wp = form.save(commit=False)
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
            wdict_url = reverse('ew.views.edit_word_pair', args=[wpid])
            message = (unicode(_('Word pair added')) +
                       ': <a href="' + wdict_url + '">' +
                       unicode(_('edit')) + '</a>')

        data = {'date_added': models.get_today(request.user),
                'date1': models.get_today(request.user),
                'date2': models.get_today(request.user),
                'strength1': 0,
                'strength2': 0}

        # Load the saved fields if they were saved not longer than 6 hours ago
        ew_add_wp_fields = request.session.get('ew_add_wp_fields')
        if ew_add_wp_fields is not None:
            saved_field, save_time = ew_add_wp_fields
            if (datetime.datetime.now() - save_time <
                datetime.timedelta(seconds=ADD_WORD_PAIR_DATE_REMEMBER_SECONDS)):
                for field, value in saved_field.items():
                    data[field] = value

        form = WordPairForm(initial=data)
    else:
        assert(False)

    set_word_pair_form_labels(wdict, form)
    return render(
               request,
               'ew/add_word_pair.html',
               {'form':  form,
                'message': message,
                'wdict': wdict})


def import_word_pairs(request, wdict, import_fun, page_title, help_text, source):

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
                "second language; explanation. The last one is optional. "
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
            for field in ('name', 'lang1', 'lang2'):
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
                          'lang2': wdict.lang2})

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
        models.calc_future(request.user, 60, models.get_today(request.user))

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
        practice_arrangement = \
            forms.ChoiceField(
                choices=practice_arrangements_choices,
                label=_('Practice page arrangement'))
        button_size = forms.IntegerField(label=_('Button size'))
        question_size = forms.IntegerField(label=_('Question size'))
        answer_size = forms.IntegerField(label=_('Answer size'))
        explanation_size = forms.IntegerField(label=_('Explanation size'))
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
                ewuser.practice_arrangement = c['practice_arrangement']
                ewuser.button_size = c['button_size']
                ewuser.question_size = c['question_size']
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
                   'button_size': ewuser.button_size,
                   'question_size': ewuser.question_size,
                   'answer_size': ewuser.answer_size,
                   'explanation_size': ewuser.explanation_size,
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
    explanation = re.sub(regexp, insert_nbps, explanation)

    return '<br/>'.join(explanation.splitlines())


def words_to_practice_to_json(words_to_practice):
    result = []
    for wp, direction in words_to_practice:

        if wp.explanation:
            expl_labels = wp.explanation
            if wp.labels:
                expl_labels += '\n\n'
        else:
            expl_labels = ''
        if wp.labels:
            expl_labels += '[%s]' % wp.labels

        result.append([escape_for_html(wp.word_in_lang1),
                       escape_for_html(wp.word_in_lang2),
                       direction,
                       wp.id,
                       escape_for_html(expl_labels, indent=True)])
    return json.dumps(result)


@wdict_access_required
@set_lang
def practice_wdict(request, wdict):
    text = 'dict: "%s"' % wdict.name
    models.log(request, 'practice_wdict', text)
    words_to_practice = wdict.get_words_to_practice_today()
    json_str = words_to_practice_to_json(words_to_practice)
    ewuser = models.get_ewuser(request.user)
    return render(request,
                  'ew/practice_wdict.html',
                  {'wdict': wdict,
                   'words_to_practice': json_str,
                   'ewuser': ewuser})


@login_required
@set_lang
def practice(request):
    models.log(request, 'practice')
    words_to_practice = request.session['ew_words_to_practice']
    json_str = words_to_practice_to_json(words_to_practice)
    ewuser = models.get_ewuser(request.user)
    return render(request,
                  'ew/practice_wdict.html',
                  {'wdict': None,
                   'words_to_practice': json_str,
                   'ewuser': ewuser})


@login_required
def update_word(request):
    try:

        answer = json.loads(request.POST['answer'])
        word_pair_id = json.loads(request.POST['word_index'])
        direction = json.loads(request.POST['direction'])

        wp = get_object_or_404(WordPair,
                               pk=word_pair_id,
                               wdict__user=request.user)

        if wp.get_date(direction) > models.get_today(request.user):
            # This update have already been performed
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

    wdict = None
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

    if 'q' not in request.GET:
        if query_wdict in ('', 'all'):
            form = SearchForm({'show_hits': True})
        else:
            wdict = get_object_or_404(WDict, pk=int(query_wdict),
                                      user=request.user)
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
            # If page is out of range (e.g. 9999), deliver last page of results.
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

        return render(request,
                      'ew/search.html',
                      {'form': form,
                       'wdict': wdict,
                       'source_url': source_url,
                       'wdict_choices': wdict_choices,
                       'show_hits': show_hits,
                       'hits_count': len(word_pairs),
                       'result_exists': True,
                       'pagination_url': pagination_url,
                       'pagination_info': pagination_info,
                       'current_page_index': current_page_index,
                       'word_pairs_and_exps': word_pairs_and_exps})


@word_pair_access_required
@set_lang
def edit_word_pair(request, wp, wdict):

    if request.method == 'POST':
        models.log(request, 'edit_word_pair')
        form = WordPairForm(request.POST)
        if form.is_valid():
            for field in models.WordPair.get_fields_to_be_edited():
                setattr(wp, field, form.cleaned_data[field])
            wp.save()
            messages.success(request, _('Word pair modified.'))
            wdict_url = reverse('ew.views.edit_word_pair', args=[wp.id])
            return HttpResponseRedirect(wdict_url)
        else:
            messages.error(request, _('Some fields are invalid.'))

    elif request.method == 'GET':
        form = WordPairForm(instance=wp)

    else:
        assert(False)

    set_word_pair_form_labels(wdict, form)
    return render(
               request,
               'ew/edit_word_pair.html',
               {'form': form,
                'word_pair': wp,
                'wdict': wdict})


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
        try:
            values = {}
            fields = ('date1', 'date2', 'strength1', 'strength2')
            for field in fields:
                raw_value = request.POST.get(field, '').strip()
                if raw_value == '':
                    value = None
                elif field.startswith('date'):
                    value = models.parse_date(raw_value)
                elif field.startswith('strength'):
                    value = int(raw_value)
                else:
                    assert(False)
                values[field] = value
            do_operation = True
        except ValueError:
            error_msg = _('Please specify the fields correctly!')
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
                wp.date1 += days
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
