from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate
from ExponWords.ew.models import Word, WordList
from django.http import Http404
from django import forms
from django.template import RequestContext


def index(request):
    user = request.user
    if user.is_authenticated():
        username = user.username
        wordlists = WordList.objects.filter(user=user)
    else:
        username = None
        wordlists = None

    return render_to_response(
               'ew/index.html',
               {'wordlists': wordlists,
                'username': username})


def auth_dict_usage(request, wordlist_id):

    user = request.user

    # If the user is not logged in, send him
    if not user.is_authenticated():
        response = render_to_response(
                       'ew/index.html',
                       {'wordlists': None,
                        'username': None})
        return {'response': response}

    # If the user does not own the word list, raise an exception
    wordlist = get_object_or_404(WordList, pk=wordlist_id)
    if wordlist.user != user:
        raise Http404

    return {'wordlist': wordlist}


def edit_wordlist(request, wordlist_id):

    auth_result = auth_dict_usage(request, wordlist_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wordlist = auth_result['wordlist']

    words = wordlist.word_set.all()

    return render_to_response(
               'ew/wordlist.html',
               {'wordlist': wordlist,
                'words': words})


def add_word_to_wordlist(wordlist, form):

    # Creating the new word
    word = Word()
    word.lang0 = form.cleaned_data['lang0']
    word.lang1 = form.cleaned_data['lang1']
    word.explanation = form.cleaned_data['explanation']

    # Adding the new word
    wordlist.word_set.add(word)
    word.save()
    wordlist.save()


class AddWordForm(forms.Form):
    lang0 = forms.CharField(max_length=255,
                            label="Word in the first language:")
    lang1 = forms.CharField(max_length=255,
                            label="Word in the second language:")
    explanation = forms.CharField(widget=forms.Textarea)


def add_word(request, wordlist_id):

    auth_result = auth_dict_usage(request, wordlist_id)
    if 'response' in auth_result:
        return auth_result['response']
    else:
        wordlist = auth_result['wordlist']

    if request.method == 'POST':
        form = AddWordForm(request.POST)
        if form.is_valid():
            add_word_to_wordlist(wordlist, form)
            message = 'Word added.'
        else:
            message = 'Some fields are invalid.'
    else:
        message = ''

    return render_to_response(
               'ew/add_word.html',
               {'form':  AddWordForm(),
                'message': message,
                'wordlist': wordlist},
                context_instance=RequestContext(request))
