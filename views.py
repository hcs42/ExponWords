from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate
from ExponWords.ew.models import Word, WordList
from django.http import Http404

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

def edit_wordlist(request, wordlist_id):

    user = request.user
    if not user.is_authenticated():
        return render_to_response(
                   'ew/index.html',
                   {'wordlists': None,
                    'username': None})

    wordlist = get_object_or_404(WordList, pk=wordlist_id)
    if wordlist.user != user:
        raise Http404

    words = wordlist.word_set.all()

    return render_to_response(
               'ew/wordlist.html',
               {'wordlist': wordlist,
                'words': words})

