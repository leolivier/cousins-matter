from django.conf import settings
from django.urls import path

from .views import views_comment, views_post, views_test, views_follow

app_name = "forum"
urlpatterns = [
    path("", views_post.PostsListView.as_view(), name="list"),
    path("page/<int:page>", views_post.PostsListView.as_view(), name="page"),
    path("create", views_post.PostCreateView.as_view(), name="create"),
    path("<int:pk>", views_post.PostDisplayView.as_view(), name="display"),
    path(
        "<int:pk>/<int:page_num>",
        views_post.PostDisplayView.as_view(),
        name="display_page",
    ),
    path("<int:pk>/edit", views_post.PostEditView.as_view(), name="edit"),
    path("<int:pk>/delete", views_post.delete_post, name="delete"),
    path("<int:pk>/reply", views_post.add_reply, name="reply"),
    path("<int:reply>/edit_reply", views_post.edit_reply, name="edit_reply"),
    path("<int:reply>/delete_reply", views_post.delete_reply, name="delete_reply"),
    path(
        "<int:message_id>/comments",
        views_comment.CommentCreateView.as_view(),
        name="add_comment",
    ),
    path(
        "comments/<int:pk>/edit",
        views_comment.CommentEditView.as_view(),
        name="edit_comment",
    ),
    path(
        "comments/<int:pk>/delete", views_comment.delete_comment, name="delete_comment"
    ),
    path("<int:pk>/toggle-follow", views_follow.toggle_follow, name="toggle_follow"),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "test/create_posts/<int:num_posts>",
            views_test.test_create_posts,
            name="test_create_posts",
        ),
        path(
            "test/create_replies/<int:num_replies>",
            views_test.test_create_replies,
            name="test_create_replies",
        ),
        path(
            "test/create_comments/<int:num_comments>",
            views_test.test_create_comments,
            name="test_create_comments",
        ),
    ]
