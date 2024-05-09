from django.urls import path

from django.contrib.auth import views as auth_views
from . import views as account_views

app_name = "accounts"
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', account_views.logout_account, name='logout'),
	path('validate_username', account_views.validate_username, name='validate_username')
]
