from django.urls import path

from .views import views_gallery, views_photo, views_bulk

app_name = "galleries"

urlpatterns = [
    path("", views_gallery.GalleryTreeView.as_view(), name="galleries"),
    path("create", views_gallery.GalleryCreateView.as_view(), name="create"),
    path("<int:pk>", views_gallery.GalleryDetailView.as_view(), name="detail"),
    path("<int:pk>/<int:page>", views_gallery.GalleryDetailView.as_view(), name="detail_page"),
    path("<int:pk>/edit", views_gallery.GalleryUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete", views_gallery.delete_gallery, name="delete_gallery"),
    path("<int:parent_gallery>/createsub", views_gallery.GalleryCreateView.as_view(), name="create_sub"),
    path("<int:gallery>/photos", views_photo.PhotoAddView.as_view(), name="add_photo"),
    path("<int:gallery>/photos/<int:photo_num>", views_photo.PhotoDetailView.as_view(), name="photo_list"),
    path("<int:gallery>/photo/<int:photo_idx>", views_photo.get_photo_url, name="gallery_photo_url"),
    path("photo/<int:pk>", views_photo.PhotoDetailView.as_view(), name="photo"),
    path("photo/<int:pk>/edit", views_photo.PhotoEditView.as_view(), name="edit_photo"),
    path("photo/<int:pk>/delete", views_photo.delete_photo, name="delete_photo"),
    path("bulk_upload", views_bulk.BulkUploadPhotosView.as_view(), name="bulk_upload"),
]
