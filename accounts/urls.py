from django.urls import path

from django.contrib.auth import views as auth_views
from . import views as account_views

app_name = "accounts"
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('register/', account_views.register, name='register'),
    path('logout/', account_views.logout_account, name='logout'),
    path('password/change/', account_views.change_password, name='change_password'),
#    path('password/change', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='change_password'),
#    path('password/changed', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change.html'), name='password_changed_done'),
]
