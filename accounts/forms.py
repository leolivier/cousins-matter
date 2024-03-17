from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, \
    PasswordChangeForm, PasswordResetForm, SetPasswordForm

class AccountRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']


class AccountUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class AccountPasswordChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']

class AccountPasswordResetForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ['email']

class AccountPasswordResetConfirmForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ['new_password1', 'new_password2']

