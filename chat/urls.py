from django.urls import path

from . import views

app_name = 'chat'
urlpatterns = [
  path('', views.chat, name='chat'),
  path('room', views.new_room, name='new_room'),
  path('room/<str:room_slug>', views.chat_room, name='room'),
]
