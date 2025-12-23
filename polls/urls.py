from django.urls import path

from polls.views import event_upsert_views

from .views import upsert_views, answer_views, display_views

app_name = "polls"
urlpatterns = [
  path("<int:pk>/", display_views.PollDetailView.as_view(), name="poll_detail"),
  path("", display_views.PollsListView.as_view(), name="list_polls"),
  path("all/", display_views.AllPollsListView.as_view(), name="all_polls"),
  path("closed/", display_views.ClosedPollsListView.as_view(), name="closed_polls"),
  path("create/", upsert_views.PollCreateView.as_view(), name="create_poll"),
  path("<int:pk>/update/", upsert_views.PollUpdateView.as_view(), name="update_poll"),
  path("<int:pk>/delete/", upsert_views.PollDeleteView.as_view(), name="delete_poll"),
  path(
    "<int:poll_id>/question/create/",
    upsert_views.QuestionCreateView.as_view(),
    name="add_question",
  ),
  path(
    "<int:poll_id>/question/<int:pk>/update/",
    upsert_views.QuestionUpdateView.as_view(),
    name="update_question",
  ),
  path("question/<int:pk>/", display_views.get_question, name="question_detail"),
  path(
    "question/<int:pk>/delete/",
    upsert_views.QuestionDeleteView.as_view(),
    name="delete_question",
  ),
  path("<int:poll_id>/vote/", answer_views.PollsVoteView.as_view(), name="vote"),
  path(
    "event-planners/<int:pk>/",
    display_views.EventPlannerDetailView.as_view(),
    name="event_planner_detail",
  ),
  path(
    "event-planners/create/",
    event_upsert_views.EventPlannerCreateView.as_view(),
    name="create_event_planner",
  ),
  path(
    "event-planners/<int:pk>/update/",
    event_upsert_views.EventPlannerUpdateView.as_view(),
    name="update_event_planner",
  ),
  path(
    "event-planners/<int:pk>/delete/",
    event_upsert_views.EventPlannerDeleteView.as_view(),
    name="delete_event_planner",
  ),
  path(
    "event-planners/",
    display_views.EventPlannersListView.as_view(),
    name="list_event_planners",
  ),
  path(
    "event-planners/all/",
    display_views.AllEventPlannersListView.as_view(),
    name="all_event_planners",
  ),
  path(
    "event-planners/closed/",
    display_views.ClosedEventPlannersListView.as_view(),
    name="closed_event_planners",
  ),
  path(
    "event-planners/<int:poll_id>/vote/",
    answer_views.EventPlannersVoteView.as_view(),
    name="event_planner_vote",
  ),
]
