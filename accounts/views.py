from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth.models import User
import base64
import logging

from .forms import AccountPasswordChangeForm, AccountPasswordResetForm, AccountPasswordResetConfirmForm

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

@login_required
def change_password(request):
  if request.method == 'POST':
    form = AccountPasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, _('Your password was successfully updated!\nPlease sign in with your new password'))
      return redirect('accounts:login')
  else:
    form = AccountPasswordChangeForm(user=request.user)
  
  context = {'form': form}
  return render(request, 'accounts/password_change.html', context)

def reset_password(request):
  if request.method == 'POST':
    form = AccountPasswordResetForm(request.POST)
    if form.is_valid():
      form.save(request=request) 
      return redirect('password_reset_done')
  else:
    form = AccountPasswordResetForm()

  context = {'form': form}
  return render(request, 'accounts/password_reset.html', context)  

def reset_password_confirm(request, uidb64, token):
  if request.method == 'POST':
    form = AccountPasswordResetConfirmForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, _('Your password has been reset!'))
      return redirect('accounts:login')
  else:
    logger.debug(uidb64, token)
    uidb64_enc = uidb64.encode('ascii')
    decoded = base64.b64decode(uidb64_enc)
    account=decoded.decode('ascii')
    form = AccountPasswordResetConfirmForm(account=account)
  
  context = {'form': form}
  return render(request, 'accounts/password_reset_confirm.html', context)
