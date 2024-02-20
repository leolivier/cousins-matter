from django.urls import path

from . import views

app_name = "members"
urlpatterns = [
    path("birthdays", views.birthdays, name="birthdays"),
    path("", views.MembersView.as_view(), name="members"),
    path("<int:pk>/", views.get_member, name="detail"),
    path("create/", views.get_member, name="create"),
#    path("<int:pk>/results/", views.ResultsView.as_view(), name="results"),
#    path("<int:question_id>/vote/", views.vote, name="vote"),
]