from django.urls import path
from django.contrib.auth import views as auth_views
from .views import views_address, views_activate, views_family, \
                  views_member, views_birthday, views_registration, \
                  views_directory, views_import, views_followers

app_name = "members"
urlpatterns = [
  path('login/', auth_views.LoginView.as_view(template_name='members/login/login.html'), name='login'),
  path('logout/', views_member.logout_member, name='logout'),
  path('validate_username', views_member.validate_username, name='validate_username'),
  path("", views_member.MembersView.as_view(), name="members"),
  path("page/<int:page_num>", views_member.MembersView.as_view(), name="members_page"),
  path("<int:pk>/", views_member.MemberDetailView.as_view(), name="detail"),
  path("<int:pk>/edit", views_member.EditMemberView.as_view(), name="member_edit"),
  path("<int:pk>/delete", views_member.delete_member, name="delete"),
  path("<int:pk>/toggle-follow", views_followers.toggle_follow, name="toggle_follow"),
  path("create/", views_member.CreateManagedMemberView.as_view(), name="create"),
  path("profile/", views_member.EditProfileView.as_view(), name="profile"),
  path("register/request", views_registration.RegistrationRequestView.as_view(), name="register_request"),
  path("register/invite", views_registration.MemberInvitationView.as_view(), name="invite"),
  path("register/<str:encoded_email>/<str:token>", views_registration.RegistrationCheckingView.as_view(), name="register"),
  path("<int:pk>/activate/", views_activate.activate_member, name="activate"),
  path("birthdays", views_birthday.birthdays, name="birthdays"),
  path("include_birthdays", views_birthday.include_birthdays, name="include_birthdays"),
  path("address/<int:pk>/", views_address.AddressDetailView.as_view(), name="address_detail"),
  path("address/create", views_address.AddressCreateView.as_view(), name="create_address"),
  path("address/<int:pk>/update", views_address.AddressUpdateView.as_view(), name="update_address"),
  path("address/modcreate", views_address.ModalAddressCreateView.as_view(), name="modal_create_address"),
  path("address/<int:pk>/modupdate", views_address.ModalAddressUpdateView.as_view(), name="modal_update_address"),
  path("family/<int:pk>/", views_family.FamilyDetailView.as_view(), name="family_detail"),
  path("family/modcreate", views_family.ModalFamilyCreateView.as_view(), name="modal_create_family"),
  path("family/<int:pk>/modupdate", views_family.ModalFamilyUpdateView.as_view(), name="modal_update_family"),
  path("family/create", views_family.FamilyCreateView.as_view(), name="create_family"),
  path("family/<int:pk>/update", views_family.FamilyUpdateView.as_view(), name="update_family"),
  path("directory", views_directory.MembersDirectoryView.as_view(), name="directory"),
  path("directory/print", views_directory.MembersPrintDirectoryView.as_view(), name="print_directory"),
  path("import", views_import.CSVImportView.as_view(), name="csv_import"),
]
