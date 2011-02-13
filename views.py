from django.shortcuts import render_to_response, get_object_or_404
from ew.models import Word, WordList
from django.contrib.auth import authenticate

def index(request):
    if request.user.is_authenticated():
        msg = 'Username: ' + request.user.username
    else:
        msg = 'Not logged in'

    wordlists = WordList.objects.all()
    return render_to_response(
               'ew/index.html',
               {'wordlists': wordlists,
                'msg': msg})

