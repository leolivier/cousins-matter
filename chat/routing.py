from django.urls import path

from .consumers import ChatConsumer

websocket_urlpatterns = [
  path("chat/<str:room_slug>", ChatConsumer.as_asgi(), name="ws_chat"),  # Using asgi
]
