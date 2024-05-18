# util functions for member views

import math
from django.forms import ValidationError
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def redirect_to_referer(request):
    if request.META.get('HTTP_REFERER'):
        return redirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect('/')


def check_file_size(file, limit):
    if file.size > limit:
        limitmb = math.floor(limit*100/(1024*1024))/100
        sizemb = math.floor(file.size*100/(1024*1024))/100
        raise ValidationError(_(f"Uploaded file is too big ({sizemb}MB), maximum is {limitmb}MB."))
