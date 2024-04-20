from django.urls import path

from . import views

app_name = "galleries"

urlpatterns = [
    path("<int:pk>", views.GalleryDisplayView.as_view(), name="display"),
    path("<int:gallery>/photos/<int:pk>", views.PhotoDetailView.as_view(), name="photo"),
    path("create", views.GalleryCreateView.as_view(), name="create"),
    path("<int:pk>/edit", views.GalleryUpdateView.as_view(), name="edit"),
    path("", views.GalleryTreeView.as_view(), name="galleries"),
    path("<int:gallery>/photos", views.PhotoAddView.as_view(), name="add_photo"),
	
]