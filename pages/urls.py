from django.urls import path

from . import views

app_name = "pages-edit"
urlpatterns = [
    path("", views.PageListView.as_view(), name="list"),
    path("create", views.PageCreateView.as_view(), name="create"),
    path("<path:page_url>/", views.PageUpdateView.as_view(), name="update"),
]
