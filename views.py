from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate
from ExponWords.ew.models import WordPair, WDict
from django.http import Http404
from django import forms
from django.template import RequestContext


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

    return render_to_response(
               'ew/view_wdict.html',
               {'wdict': wdict,
                'word_pairs': word_pairs})


def add_word_pair_to_wdict(wdict, form):

    # Creating the new word
    wp = WordPair()
    wp.word_in_lang1 = form.cleaned_data['word_in_lang1']
    wp.word_in_lang2 = form.cleaned_data['word_in_lang2']
    wp.explanation = form.cleaned_data['explanation']

    # Adding the new word
    wdict.wordpair_set.add(wp)
    wp.save()
    wdict.save()


def add_word_pair(request, wdict_id):

    auth_result = auth_dict_usage(request, wdict_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wdict = auth_result['wdict']

    label1 = 'Word in "%s":' % (wdict.lang1,)
    label2 = 'Word in "%s":' % (wdict.lang2,)
    class AddWordPairForm(forms.Form):
        word_in_lang1 = forms.CharField(max_length=255, label=label1)
        word_in_lang2 = forms.CharField(max_length=255, label=label2)
        explanation = forms.CharField(widget=forms.Textarea)

    if request.method == 'POST':
        form = AddWordPairForm(request.POST)
        if form.is_valid():
            add_word_pair_to_wdict(wdict, form)
            message = 'Word pair added.'
        else:
            message = 'Some fields are invalid.'
    else:
        message = ''

    return render_to_response(
               'ew/add_word_pair.html',
               {'form':  AddWordPairForm(),
                'message': message,
                'wdict': wdict},
                context_instance=RequestContext(request))


def modify_word_pair(word_pair, form):

    # Creating the new word
    wp = word_pair
    wp.word_in_lang1 = form.cleaned_data['word_in_lang1']
    wp.word_in_lang2 = form.cleaned_data['word_in_lang2']
    wp.explanation = form.cleaned_data['explanation']
    wp.save()


def edit_word_pair(request, word_pair_id):

    auth_result = auth_word_pair_usage(request, word_pair_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wp = auth_result['word_pair']
        wdict = auth_result['wdict']

    label1 = 'Word in "%s":' % (wdict.lang1,)
    label2 = 'Word in "%s":' % (wdict.lang2,)
    class EditWordPairForm(forms.Form):
        word_in_lang1 = forms.CharField(max_length=255, label=label1)
        word_in_lang2 = forms.CharField(max_length=255, label=label2)
        explanation = forms.CharField(widget=forms.Textarea)

    if request.method == 'POST':
        form = EditWordPairForm(request.POST)
        if form.is_valid():
            modify_word_pair(wp, form)
            message = 'Word pair modified.'
        else:
            message = 'Some fields are invalid.'
    else:
        message = ''
        data = {'word_in_lang1': wp.word_in_lang1,
                'word_in_lang2': wp.word_in_lang2,
                'explanation': wp.explanation}
        form = EditWordPairForm(data)

    return render_to_response(
               'ew/edit_word_pair.html',
               {'form': form,
                'message': message,
                'word_pair': wp},
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
