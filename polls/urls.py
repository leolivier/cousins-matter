from django.urls import path

from .views import upsert_views, answer_views

app_name = "polls"
urlpatterns = [
    path("", upsert_views.PollsListView.as_view(), name="list_polls"),
    path("<int:pk>/", upsert_views.PollDetailView.as_view(), name="poll_detail"),
    path("all/", upsert_views.AllPollsListView.as_view(), name="all_polls"),
    path("closed/", upsert_views.ClosedPollsListView.as_view(), name="closed_polls"),
    path("create/", upsert_views.PollCreateView.as_view(), name="create_poll"),
    path("<int:pk>/update/", upsert_views.PollUpdateView.as_view(), name="update_poll"),
    path("<int:pk>/delete/", upsert_views.PollDeleteView.as_view(), name="delete_poll"),
    path("<int:poll_id>/question/create/", upsert_views.QuestionCreateView.as_view(), name="add_question"),
    path("<int:poll_id>/question/<int:pk>/update/", upsert_views.QuestionUpdateView.as_view(),
         name="update_question"),
    path("question/<int:pk>/", upsert_views.get_question, name="question_detail"),
    # path("<int:pk>/question/delete/", upsert_views.QuestionDeleteView.as_view(), name="delete_question"),
    # path("<int:pk>/answer/", answer_views.PollAnswerView.as_view(), name="answer"),
    path("<int:poll_id>/results/", answer_views.PollResultsView.as_view(), name="results"),
    path("<int:poll_id>/vote/", answer_views.PollsVoteView.as_view(), name="vote"),
    # path("question/<int:question_id>/vote/", answer_views.vote, name="vote_question"),
]
