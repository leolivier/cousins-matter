from django.urls import path

from . import views

app_name = "pages-edit"
urlpatterns = [
    path("", views.PageTreeView.as_view(), name="tree"),
    path("admin", views.PageAdminListView.as_view(), name="edit_list"),
    path("create", views.PageCreateView.as_view(), name="create"),
    path("<int:pk>", views.PageUpdateView.as_view(), name="update"),
]
