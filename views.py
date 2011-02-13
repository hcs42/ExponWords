from django.shortcuts import render_to_response, get_object_or_404
from ew.models import Word, WordList
from django.contrib.auth import authenticate

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

