from django.urls import path

from . import views

app_name = "news"
urlpatterns = [
    path("", views.NewsListView.as_view(), name="list"),
    path("page/<int:page>", views.NewsListView.as_view(), name="page"),
    path("create", views.NewsCreateView.as_view(), name="create"),
    path("<int:pk>", views.NewsDisplayView.as_view(), name="display"),
    path("<int:pk>/edit", views.NewsEditView.as_view(), name="edit"),
    path("<int:pk>/delete", views.NewsDeleteView.as_view(), name="delete"),
    path("<int:pk>/reply", views.add_reply, name="reply"),
    path("<int:reply>/edit_reply", views.edit_reply, name="edit_reply"),
    path("<int:reply>/delete_reply", views.delete_reply, name="delete_reply"),
    path("<int:content_id>/comments", views.CommentCreateView.as_view(), name="create_comment"),
    path("comments/<int:pk>/edit", views.CommentEditView.as_view(), name="edit_comment"),
    path("comments/<int:pk>/delete", views.delete_comment, name="delete_comment"),
]
