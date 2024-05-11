from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


def validate_username(request):
    """Check username availability"""
    username = request.GET.get('username', None)
    response = {
        'is_taken': username != request.user.username and User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(response)


@login_required
def logout_account(request):
    logout(request)
    messages.success(request, _("You have been logged out"))
    return redirect('accounts:login')
