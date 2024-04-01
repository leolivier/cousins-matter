from django.urls import path

from . import views

app_name = "members"
urlpatterns = [
    path("birthdays", views.birthdays, name="birthdays"),
    path("", views.MembersView.as_view(), name="members"),
    path("<int:pk>/", views.display_member, name="detail"),
    path("create/", views.create_member, name="create"),
	path("profile/", views.profile, name="profile"),
	path("register/", views.register_member, name="register"),
	path("<int:pk>/activate/", views.activate_account, name="activate"),
]