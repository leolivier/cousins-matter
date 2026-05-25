from django.urls import path

from .views import views_gallery, views_photo, views_bulk

app_name = "galleries"

urlpatterns = [
  path("", views_gallery.GalleryTreeView.as_view(), name="galleries"),
  path("create", views_gallery.GalleryCreateView.as_view(), name="create"),
  path("photo/<int:pk>", views_photo.PhotoDetailView.as_view(), name="photo"),
  path("photo/<int:pk>/edit", views_photo.PhotoEditView.as_view(), name="edit_photo"),
  path("photo/<int:pk>/delete", views_photo.delete_photo, name="delete_photo"),
  path("bulk_upload", views_bulk.BulkUploadPhotosView.as_view(), name="bulk_upload"),
  path("upload_progress/<str:id>", views_bulk.upload_progress, name="upload_progress"),
  path(
    "photo/<int:pk>/fullscreen",
    views_photo.get_fullscreen_photo,
    name="get_fullscreen_photo",
  ),
  path("<slug:slug>", views_gallery.GalleryDetailView.as_view(), name="detail"),
  path(
    "<slug:slug>/<int:page>",
    views_gallery.GalleryDetailView.as_view(),
    name="detail_page",
  ),
  path("<slug:slug>/edit", views_gallery.GalleryUpdateView.as_view(), name="edit"),
  path("<slug:slug>/delete", views_gallery.delete_gallery, name="delete_gallery"),
  path(
    "<slug:parent_gallery>/createsub",
    views_gallery.GalleryCreateView.as_view(),
    name="create_sub",
  ),
  path("<slug:gallery>/photos", views_photo.PhotoAddView.as_view(), name="add_photo"),
]
