from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate
from ExponWords.ew.models import WordPair, WDict
import ExponWords.ew.models as models
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django import forms
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
import datetime
import json
import traceback
import re
import sys


def index(request):
    user = request.user
    if user.is_authenticated():
        username = user.username
        wdicts = WDict.objects.filter(user=user, deleted=False)
    else:
        username = None
        wdicts = None

    return render_to_response(
               'ew/index.html',
               {'wdicts': wdicts,
                'username': username})


def options(request):
    return render_to_response(
               'ew/options.html',
               {},
               context_instance=RequestContext(request))


def help(request, lang):
    langs = [langcode for langcode, langname in settings.LANGUAGES]
    print 'lang:', lang
    print 'langs:', langs
    if lang in langs:
        return render_to_response(
                   'ew/help/%s.html' % lang,
                   {'version': models.version})
    else:
        raise Http404


def auth_user(request):
    if not request.user.is_authenticated():
        return False
    else:
        return True


def auth_dict_usage(request, wdict_id):

    if not auth_user(request):
        return {'response': HttpResponseRedirect('/')}

    # Get the dictionary; of it does not exist, send him to page 404
    wdict = get_object_or_404(WDict, pk=wdict_id)

    # If the user does not own the dictionary, send him to page 404
    if wdict.user != request.user:
        raise Http404

    return {'wdict': wdict}


def auth_word_pair_usage(request, word_pair_id):

    if not auth_user(request):
        return {'response': HttpResponseRedirect('/')}

    # Get the dictionary; of it does not exist, send him to page 404
    wp = get_object_or_404(WordPair, pk=word_pair_id)
    wdict = wp.wdict

    # If the user does not own the dictionary, send him to page 404
    if wp.wdict.user != request.user:
        raise Http404

    return {'word_pair': wp,
            'wdict': wdict}


def wdict(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    return render_to_response(
               'ew/wdict.html',
               {'wdict': wdict})


def view_wdict(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    word_pairs = wdict.wordpair_set.filter(deleted=False)
    word_pairs_and_exps = []
    for wp in word_pairs:
        word_pairs_and_exps.append((wp, explanation_to_html(wp.explanation)))

    lang_label1 = (_('Word in "%(lang)s"') % {'lang': wdict.lang1})
    lang_label2 = (_('Word in "%(lang)s"') % {'lang': wdict.lang2})

    return render_to_response(
               'ew/view_wdict.html',
               {'wdict': wdict,
                'word_pairs_and_exps': word_pairs_and_exps,
                'lang_label1': lang_label1,
                'lang_label2': lang_label2},
                context_instance=RequestContext(request))

def CreateWordPairForm(wdict):

    label1 = (_('Word in "%(lang)s"') % {'lang': wdict.lang1}) + ':'
    label2 = (_('Word in "%(lang)s"') % {'lang': wdict.lang2}) + ':'
    label_date_added = _('Date of addition') + ':'
    label_date1 = _('Date of next practice from "%(lang)s"') % {'lang': wdict.lang1} + ':'
    label_date2 = _('Date of next practice from "%(lang)s"') % {'lang': wdict.lang2} + ':'
    label_strength1 = _('Strengh of word from "%(lang)s"') % {'lang': wdict.lang1} + ':'
    label_strength2 = _('Strengh of word from "%(lang)s"') % {'lang': wdict.lang2} + ':'

    class WordPairForm(forms.Form):
        word_in_lang1 = forms.CharField(max_length=255, label=label1)
        word_in_lang2 = forms.CharField(max_length=255, label=label2)
        explanation = forms.CharField(widget=forms.Textarea, required=False)
        date_added = forms.DateField(label=label_date_added)
        date1 = forms.DateField(label=label_date1)
        date2 = forms.DateField(label=label_date2)
        strength1 = forms.IntegerField(label=label_strength1)
        strength2 = forms.IntegerField(label=label_strength2)

    return WordPairForm


def set_word_pair_from_form(word_pair, form):

    # Creating the new word
    word_pair.word_in_lang1 = form.cleaned_data['word_in_lang1']
    word_pair.word_in_lang2 = form.cleaned_data['word_in_lang2']
    word_pair.explanation = form.cleaned_data['explanation']
    word_pair.date_added = form.cleaned_data['date_added']
    word_pair.date1 = form.cleaned_data['date1']
    word_pair.date2 = form.cleaned_data['date2']
    word_pair.strength1 = form.cleaned_data['strength1']
    word_pair.strength2 = form.cleaned_data['strength2']


def add_word_pair(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    AddWordPairForm = CreateWordPairForm(wdict)
    if request.method == 'POST':
        form = AddWordPairForm(request.POST)
        if form.is_valid():

            wp = WordPair()
            set_word_pair_from_form(wp, form)
            wdict.wordpair_set.add(wp)
            wp.save()
            wdict.save()

            message = _('Word pair added.')
            form = None
        else:
            message = _('Some fields are invalid.')
    else:
        form = None
        message = ''

    if form is None:
        data = {'date_added': datetime.date.today(),
                'date1': datetime.date.today(),
                'date2': datetime.date.today(),
                'strength1': 0,
                'strength2': 0}
        form = AddWordPairForm(data)

    return render_to_response(
               'ew/add_word_pair.html',
               {'form':  form,
                'message': message,
                'wdict': wdict},
                context_instance=RequestContext(request))


def edit_word_pair(request, word_pair_id):

    auth_result = auth_word_pair_usage(request, word_pair_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wp = auth_result['word_pair']
        wdict = auth_result['wdict']

    EditWordPairForm = CreateWordPairForm(wdict)
    if request.method == 'POST':
        form = EditWordPairForm(request.POST)
        if form.is_valid():
            set_word_pair_from_form(wp, form)
            wp.save()
            message = _('Word pair modified.')
        else:
            message = _('Some fields are invalid.')
    else:
        message = ''
        data = {'word_in_lang1': wp.word_in_lang1,
                'word_in_lang2': wp.word_in_lang2,
                'explanation': wp.explanation,
                'date_added': wp.date_added,
                'date1': wp.date1,
                'date2': wp.date2,
                'strength1': wp.strength1,
                'strength2': wp.strength2}
        form = EditWordPairForm(data)

    return render_to_response(
               'ew/edit_word_pair.html',
               {'form': form,
                'message': message,
                'word_pair': wp,
                'wdict': wdict},
                context_instance=RequestContext(request))


def add_wdict(request):

    if not auth_user(request):
        return HttpResponseRedirect('/')

    class AddWDictForm(forms.Form):
        name = forms.CharField(max_length=255,
                               label=_("Name of the dictionary") + ':')
        lang1 = forms.CharField(max_length=255,
                                label=_("Language 1") + ':')
        lang2 = forms.CharField(max_length=255,
                                label=_("Language 2") + ':')

    if request.method == 'POST':
        form = AddWDictForm(request.POST)
        if form.is_valid():
            wdict = WDict()
            wdict.user = request.user
            wdict.name = form.cleaned_data['name']
            wdict.lang1 = form.cleaned_data['lang1']
            wdict.lang2 = form.cleaned_data['lang2']
            wdict.save()
            message = _('Dictionary created.')
        else:
            message = _('Some fields are invalid.')
    else:
        message = ''

    return render_to_response(
               'ew/add_wdict.html',
               {'form':  AddWDictForm(),
                'message': message},
                context_instance=RequestContext(request))


def practice_wdict(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    return render_to_response(
               'ew/practice_wdict.html',
               {'wdict': wdict,
                'message': ''},
                context_instance=RequestContext(request))


def explanation_to_html(explanation):
    """Escapes the given explanation so that it can be printed as HTML.

    **Argument:**

    - `explanation` (str)

    **Returns:** str
    """

    def insert_nbps(matchobject):
        """Returns the same number of "&nbsp;":s as the number of matched
        characters."""
        spaces = matchobject.group(1)
        return '&nbsp;' * (4 + len(spaces))

    regexp = re.compile(r'^( *)', re.MULTILINE)
    if (len(explanation) > 1) and (explanation[-1] == '\n'):
        explanation = explanation[:-1]
    exp2 = re.sub(regexp, insert_nbps, explanation)
    exp3 = '<br/>'.join(exp2.splitlines())
    return exp3


def get_words_to_practice_today(request, wdict_id):

    try:
        auth_result = auth_dict_usage(request, wdict_id)
        if 'response' in auth_result:
            return auth_result['response']
        else:
            wdict = auth_result['wdict']

        words_to_practice = wdict.get_words_to_practice_today()
    
        result = []
        for wp, direction in words_to_practice:
            result.append([wp.word_in_lang1,
                           wp.word_in_lang2,
                           direction,
                           wp.id,
                           explanation_to_html(wp.explanation)])
    
        return HttpResponse(json.dumps(result),
                             mimetype='application/json')
    except Exception, e:
        traceback.print_stack()
        exc_info = sys.exc_info()
        traceback.print_exception(exc_info[0], exc_info[1], exc_info[2])
        raise exc_info[0], exc_info[1], exc_info[2]


def update_word(request, wdict_id):
    try:

        answer = json.loads(request.POST['answer'])
        word_pair_id = json.loads(request.POST['word_index'])
        direction = json.loads(request.POST['direction'])

        auth_result = auth_word_pair_usage(request, word_pair_id)
        if 'response' in auth_result:
            return auth_result['response']
        else:
            wp = auth_result['word_pair']
            wdict = auth_result['wdict']

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


def delete_word_pairs(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    word_pairs = wdict.wordpair_set.filter(deleted=False)
    word_pairs_to_delete = []
    for wp in word_pairs:
        if unicode(wp.id) in request.POST:
            word_pairs_to_delete.append(wp)
    print word_pairs_to_delete

    for wp in word_pairs_to_delete:
        wp.deleted = True
        wp.save()

    return HttpResponseRedirect('../view/')


def CreateImportWordPairsForm(wdict):

    class ImportForm(forms.Form):
         text = forms.CharField(widget=forms.Textarea, label=_("Text") + ':')

    return ImportForm


def import_word_pairs(request, wdict_id, import_fun, page_title, help_text):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    ImportForm = CreateImportWordPairsForm(wdict)
    if request.method == 'POST':
        form = ImportForm(request.POST)
        if form.is_valid():
            try:
                import_fun(form.cleaned_data['text'], wdict)
                message = _('Word pairs added.')
                form = None
            except Exception, e:
                message = _('Error: ') + unicode(e)
        else:
            message = _('Some fields are invalid.')
    else:
        form = None
        message = ''

    if form is None:
        form = ImportForm()

    return render_to_response(
               'ew/import_word_pairs.html',
               {'form':  form,
                'help_text': help_text,
                'message': message,
                'wdict': wdict,
                'page_title': page_title},
                context_instance=RequestContext(request))


def import_word_pairs_from_text(request, wdict_id):

    page_title = _('Import word pairs from text')
    help_text = ""
    return import_word_pairs(request, wdict_id, models.import_textfile,
                             page_title, help_text)


def import_word_pairs_from_tsv(request, wdict_id):

    page_title = _('Import word pairs from tab-separated values')
    help_text = _("Write one word per line. Each word should contain two or "
                "three fields: word in the first language; word in the "
                "second language; explanation. The last one is optional. "
                "The fields should be separated by a TAB character. If a "
                "spreadsheet is opened in as spreadsheet editor application "
                "(such as LibreOffice, OpenOffice.org or Mircosoft Excel), "
                "and it contains these three columns, which are copied and "
                "pasted here, then it will have exactly this format.")
    return import_word_pairs(request, wdict_id, models.import_tsv,
                             page_title, help_text)


def export_word_pairs_to_text(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    text = models.export_textfile(wdict)

    return render_to_response(
               'ew/export_wdict_as_text.html',
               {'wdict': wdict,
                'text': text})


def CreateDeleteWDictForm(wdict):
    label = (_('Are you sure that you want to delete dictionary "%(wdict)s"?') %
             {'wdict': wdict.name})
    class DeleteWDictForm(forms.Form):
         sure = forms.BooleanField(label=label, required=False)
    return DeleteWDictForm


def delete_wdict(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    DeleteWDictForm = CreateDeleteWDictForm(wdict)
    if request.method == 'POST':
        form = DeleteWDictForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['sure']:
                wdict.deleted = True
                wdict.save()
                message = _('Dictionary deleted.')
                form = None
            else:
                message = _('Please check in the "Are you sure" checkbox if '
                            'you really want to delete the dictionary.')
        else:
            message = _('Some fields are invalid.')
    else:
        form = None
        message = ''

    if form is None:
        form = DeleteWDictForm()

    return render_to_response(
               'ew/delete_wdict.html',
               {'form':  form,
                'message': message,
                'wdict': wdict},
                context_instance=RequestContext(request))
