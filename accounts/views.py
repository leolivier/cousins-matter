from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AccountRegisterForm, AccountUpdateForm, \
    AccountPasswordChangeForm, AccountPasswordResetForm, \
    AccountPasswordResetConfirmForm
from django.utils.translation import gettext as _
from django.contrib.auth import logout
import base64
import logging

logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = AccountRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, _('Hello %(username)s, your account has been created! You are now able to log in') % {"username": username})
            return redirect('accounts:login')
    else:
        form = AccountRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

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
      messages.success(request, _('Your password was successfully updated!\nPlease login with your new password'))
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
