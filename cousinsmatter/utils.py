# util functions for member views

from django.shortcuts import redirect


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def redirect_to_referer(request):
    if request.META.get('HTTP_REFERER'):
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect('/')
