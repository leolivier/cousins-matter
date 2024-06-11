from django.conf import settings
from django.urls import path

from . import views

app_name = 'chat'
urlpatterns = [
  path('', views.chat, name='chat'),
  path('<int:page_num>', views.chat, name='chat_page'),
  path('room', views.new_room, name='new_room'),
  path('room/<str:room_slug>', views.chat_room, name='room'),
  path('room/<str:room_slug>/<int:page_num>', views.chat_room, name='room_page'),
]
if settings.DEBUG:
  urlpatterns += [
    path('test/create_rooms/<int:num_rooms>', views.test_create_rooms, name='test_create_rooms'),
    path('test/create_messages/<int:num_messages>', views.test_create_messages, name='test_create_messages'),
  ]
