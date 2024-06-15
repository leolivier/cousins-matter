from django.conf import settings
from django.urls import path

from . import views

app_name = "forum"
urlpatterns = [
    path("", views.PostsListView.as_view(), name="list"),
    path("page/<int:page>", views.PostsListView.as_view(), name="page"),
    path("create", views.PostCreateView.as_view(), name="create"),
    path("<int:pk>", views.PostDisplayView.as_view(), name="display"),
    path("<int:pk>/<int:page_num>", views.PostDisplayView.as_view(), name="display_page"),
    path("<int:pk>/edit", views.PostEditView.as_view(), name="edit"),
    path("<int:pk>/delete", views.delete_post, name="delete"),
    path("<int:pk>/reply", views.add_reply, name="reply"),
    path("<int:reply>/edit_reply", views.edit_reply, name="edit_reply"),
    path("<int:reply>/delete_reply", views.delete_reply, name="delete_reply"),
    path("<int:message_id>/comments", views.CommentCreateView.as_view(), name="add_comment"),
    path("comments/<int:pk>/edit", views.CommentEditView.as_view(), name="edit_comment"),
    path("comments/<int:pk>/delete", views.delete_comment, name="delete_comment"),
]

if settings.DEBUG:
  urlpatterns += [
    path("test/create_posts/<int:num_posts>", views.test_create_posts, name="test_create_posts"),
    path("test/create_replies/<int:num_replies>", views.test_create_replies, name="test_create_replies"),
    path("test/create_comments/<int:num_comments>", views.test_create_comments, name="test_create_comments"),
  ]
