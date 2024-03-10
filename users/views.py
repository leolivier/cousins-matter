from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, \
    ProfileUpdateForm, UserPasswordChangeForm, \
    UserPasswordResetForm, UserPasswordResetConfirmForm
from django.utils.translation import gettext as _
from django.contrib.auth import logout
import base64

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, _('Hello %(username)s, your account has been created! You are now able to log in') % {"username": username})
            return redirect('users:login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, _("You have been logged out"))
    return redirect('users:login')

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, _('Your account has been updated!'))
            return redirect('users:profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)

@login_required
def change_password(request):
  if request.method == 'POST':
    form = UserPasswordChangeForm(user=request.user, data=request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, _('Your password was successfully updated!\nPlease login with your new password'))
      return redirect('users:profile')
  else:
    form = UserPasswordChangeForm(user=request.user)
  
  context = {'form': form}
  return render(request, 'users/password_change.html', context)

def reset_password(request):
  if request.method == 'POST':
    form = UserPasswordResetForm(request.POST)
    if form.is_valid():
      form.save(request=request) 
      return redirect('password_reset_done')
  else:
    form = UserPasswordResetForm()

  context = {'form': form}
  return render(request, 'users/password_reset.html', context)  

def reset_password_confirm(request, uidb64, token):
  if request.method == 'POST':
    form = UserPasswordResetConfirmForm(request.POST)
    if form.is_valid():
      user = form.save()
      messages.success(request, _('Your password has been reset!'))
      return redirect('users:login')
  else:
    print(uidb64, token)
    uidb64_enc = uidb64.encode('ascii')
    decoded = base64.b64decode(uidb64_enc)
    user=decoded.decode('ascii')
    form = UserPasswordResetConfirmForm(user=user)
  
  context = {'form': form}
  return render(request, 'users/password_reset_confirm.html', context)
