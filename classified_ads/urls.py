from django.urls import path

from . import views

app_name = "classified_ads"
urlpatterns = [
  path("", views.ListAdsView.as_view(), name="list"),
  path("create", views.CreateAdView.as_view(), name="create"),
  path("<int:pk>/detail", views.AdDetailView.as_view(), name="detail"),
  path("<int:pk>/update", views.UpdateAdView.as_view(), name="update"),
  path("<int:pk>/delete", views.DeleteAdView.as_view(), name="delete"),
  path("<int:pk>/photo", views.AdPhotoAddView.as_view(), name="add_photo"),
  path("photo/<int:pk>/delete", views.delete_photo, name="delete_photo"),
  path("<int:pk>/send-message", views.send_message, name="send_message"),
  path("photo/<int:pk>/fullscreen", views.get_fullscreen_photo, name="get_fullscreen_photo"),
  path("subcategories", views.get_subcategories, name="get_subcategories"),
]
