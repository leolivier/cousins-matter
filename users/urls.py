from django.urls import path

from django.contrib.auth import views as auth_views
from . import views as user_views

app_name = "users"
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),
    path('logout/', user_views.logout_user, name='logout'),
    path('password/change/', user_views.change_password, name='change_password'),
#    path('password/reset/', user_views.reset_password, name='reset_password'),
#    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
#    path('password/change', auth_views.PasswordChangeView.as_view(template_name='users/password_change.html'), name='change_password'),
#    path('password/changed', auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change.html'), name='password_changed_done'),
]
