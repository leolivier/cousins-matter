from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class AccountRegisterForm(UserCreationForm):
     class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']

class AccountUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

