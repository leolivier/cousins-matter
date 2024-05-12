from django.urls import path

from .views import views_gallery, views_photo, views_bulk

app_name = "galleries"

urlpatterns = [
    path("<int:pk>", views_gallery.GalleryDisplayView.as_view(), name="display"),
    path("create", views_gallery.GalleryCreateView.as_view(), name="create"),
    path("<int:pk>/edit", views_gallery.GalleryUpdateView.as_view(), name="edit"),
    path("", views_gallery.GalleryTreeView.as_view(), name="galleries"),
    path("<int:gallery>/photos", views_photo.PhotoAddView.as_view(), name="add_photo"),
    path("<int:gallery>/photos/<int:pk>", views_photo.PhotoDetailView.as_view(), name="photo"),
    path("<int:gallery>/photos/<int:pk>/edit", views_photo.PhotoEditView.as_view(), name="edit_photo"),
    path("<int:gallery>/photos/<int:pk>/delete", views_photo.delete_photo, name="delete_photo"),
    path("bulk_upload", views_bulk.BulkUploadPhotosView.as_view(), name="bulk_upload"),
]
