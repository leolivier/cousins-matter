from django.urls import path

from . import consumers

websocket_urlpatterns = [
  path('chat/<str:room_slug>', consumers.ChatConsumer.as_asgi(), name="ws_chat"),  # Using asgi
]
