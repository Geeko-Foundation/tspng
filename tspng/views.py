import logging
logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

#@login_required
def home(request, pagetitle="static", topic=''):
    return render(request, 'home.html', {})

def test(request, pagetitle="static", topic=''):
    return render(request, 'test2.html', {})
