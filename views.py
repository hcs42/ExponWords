from django.shortcuts import render_to_response, get_object_or_404
from ew.models import Word, WordList
from django.contrib.auth import authenticate

def index(request):
    if request.user.is_authenticated():
        username = request.user.username
        wordlists = WordList.objects.all()
    else:
        username = None
        wordlists = None

    return render_to_response(
               'ew/index.html',
               {'wordlists': wordlists,
                'username': username})

