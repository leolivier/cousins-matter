from django.urls import path
from . import views

app_name = "troves"

urlpatterns = [
    path('', views.trove_cave, name='list'),
    path("page/<int:page>", views.trove_cave, name="page"),
    path('create/', views.create_treasure, name='create'),
    path('<int:pk>/update/', views.update_treasure, name='update'),
    path('<int:pk>/delete/', views.delete_treasure, name='delete'),
]
