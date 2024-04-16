from django.urls import path

from . import views
from .views import views_address, views_activate, views_family, views_member, views_birthday, views_checkregister, views_directory

app_name = "members"
urlpatterns = [
	path("", views_member.MembersView.as_view(), name="members"),
	path("<int:pk>/", views_member.display_member, name="detail"),
	path("create/", views_member.create_member, name="create"),
	path("profile/", views_member.profile, name="profile"),
	path("register/request", views_checkregister.register_request, name="register_request"),
	path("register/invite", views_checkregister.send_registration_invitation, name="invite"),
	path("register/<str:encoded_email>/<str:token>", views_checkregister.check_register, name="register"),
	path("<int:pk>/activate/", views_activate.activate_account, name="activate"),
	path("birthdays", views_birthday.birthdays, name="birthdays"),
	path("include_birthdays", views_birthday.include_birthdays, name="include_birthdays"),
	path("address/create", views_address.AddressCreateView.as_view(), name="create_address"),
	path("address/<int:pk>/", views_address.AddressDetailView.as_view(), name="address_detail"),
	path("address/<int:pk>/update", views_address.AddressUpdateView.as_view(), name="update_address"),
	path("family/create", views_family.FamilyCreateView.as_view(), name="create_family"),
	path("family/<int:pk>/", views_family.FamilyDetailView.as_view(), name="family_detail"),
	path("family/<int:pk>/update", views_family.FamilyUpdateView.as_view(), name="update_family"),
	path("directory", views_directory.MembersDirectoryView.as_view(), name="directory"),
	path("directory/print", views_directory.MembersPrintDirectoryView.as_view(), name="print_directory"),
]