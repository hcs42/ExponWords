from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate
from ExponWords.ew.models import WordPair, WDict
import ExponWords.ew.models as models
from django.http import Http404, HttpResponse
from django import forms
from django.template import RequestContext
import datetime
import json
import traceback
import re
import sys


def index(request):
    user = request.user
    if user.is_authenticated():
        username = user.username
        wdicts = WDict.objects.filter(user=user)
    else:
        username = None
        wdicts = None

    return render_to_response(
               'ew/index.html',
               {'wdicts': wdicts,
                'username': username})


def auth_user(request):

    # If the user is not logged in, send him to the index page
    if not request.user.is_authenticated():
        response = render_to_response(
                       'ew/index.html',
                       {'wdicts': None,
                        'username': None})
        return {'response': response}

    return {}


def auth_dict_usage(request, wdict_id):

    auth_result = auth_user(request)
    if 'response' in auth_result:
        # TODO redirect
        return auth_result['response']

    # Get the dictionary; of it does not exist, send him to page 404
    wdict = get_object_or_404(WDict, pk=wdict_id)

    # If the user does not own the dictionary, send him to page 404
    if wdict.user != request.user:
        raise Http404

    return {'wdict': wdict}


def auth_word_pair_usage(request, word_pair_id):

    auth_result = auth_user(request)
    if 'response' in auth_result:
        return auth_result['response']

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

    word_pairs = wdict.wordpair_set.all()
    word_pairs_and_exps = []
    for wp in word_pairs:
        word_pairs_and_exps.append((wp, explanation_to_html(wp.explanation)))

    return render_to_response(
               'ew/view_wdict.html',
               {'wdict': wdict,
                'word_pairs_and_exps': word_pairs_and_exps})

def CreateWordPairForm(wdict):

    label1 = 'Word in "%s":' % (wdict.lang1,)
    label2 = 'Word in "%s":' % (wdict.lang2,)
    label_date_added = 'Date of addition:'
    label_date1 = 'Date of next practice from "%s":' % (wdict.lang1,)
    label_date2 = 'Date of next practice from "%s":' % (wdict.lang2,)
    label_strength1 = 'Strengh of word from "%s":' % (wdict.lang1,)
    label_strength2 = 'Strengh of word from "%s":' % (wdict.lang2,)

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

            message = 'Word pair added.'
            form = None
        else:
            message = 'Some fields are invalid.'
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
            message = 'Word pair modified.'
        else:
            message = 'Some fields are invalid.'
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

    auth_result = auth_user(request)
    if 'response' in auth_result:
        return auth_result['response']

    class AddWDictForm(forms.Form):
        name = forms.CharField(max_length=255, label="Name of the dictionary:")
        lang1 = forms.CharField(max_length=255, label="Language 1:")
        lang2 = forms.CharField(max_length=255, label="Language 2:")

    if request.method == 'POST':
        form = AddWDictForm(request.POST)
        if form.is_valid():
            wdict = WDict()
            wdict.user = request.user
            wdict.name = form.cleaned_data['name']
            wdict.lang1 = form.cleaned_data['lang1']
            wdict.lang2 = form.cleaned_data['lang2']
            wdict.save()
            message = 'Dictionary created.'
        else:
            message = 'Some fields are invalid.'
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
    print 'update_word start'
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


def CreateImportWordPairsFromTextForm(wdict):

    class ImportForm(forms.Form):
         text = forms.CharField(widget=forms.Textarea)

    return ImportForm


def import_word_pairs_from_text(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    ImportForm = CreateImportWordPairsFromTextForm(wdict)
    if request.method == 'POST':
        form = ImportForm(request.POST)
        if form.is_valid():
            try:
                models.import_textfile(form.cleaned_data['text'], wdict)
                message = 'Word pairs added.'
                form = None
            except Exception, e:
                message = 'Error: ' + str(e)
        else:
            message = 'Some fields are invalid.'
    else:
        form = None
        message = ''

    if form is None:
        form = ImportForm()

    return render_to_response(
               'ew/import_word_pairs_from_text.html',
               {'form':  form,
                'message': message,
                'wdict': wdict},
                context_instance=RequestContext(request))
