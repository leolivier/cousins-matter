from django.urls import path

from django.contrib.auth import views as auth_views
from . import views as user_views

app_name = "users"
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('logout/', user_views.logout_user, name='logout'),
]
