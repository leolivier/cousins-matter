from django.urls import path

from . import views
from .views import views_address, views_activate, views_family, views_member, views_birthday

app_name = "members"
urlpatterns = [
	path("birthdays", views_birthday.birthdays, name="birthdays"),
	path("", views_member.MembersView.as_view(), name="members"),
	path("<int:pk>/", views_member.display_member, name="detail"),
	path("create/", views_member.create_member, name="create"),
	path("profile/", views_member.profile, name="profile"),
	path("register/", views_member.register_member, name="register"),
	path("<int:pk>/activate/", views_activate.activate_account, name="activate"),
	path("address/create", views_address.AddressCreateView.as_view(), name="create_address"),
	path("address/<int:pk>/", views_address.AddressDetailView.as_view(), name="address_detail"),
	path("address/<int:pk>/update", views_address.AddressUpdateView.as_view(), name="update_address"),
	path("family/create", views_family.FamilyCreateView.as_view(), name="create_family"),
	path("family/<int:pk>/", views_family.FamilyDetailView.as_view(), name="family_detail"),
	path("family/<int:pk>/update", views_family.FamilyUpdateView.as_view(), name="update_family"),
	path("include_birthdays", views_birthday.include_birthdays, name="include_birthdays"),
]