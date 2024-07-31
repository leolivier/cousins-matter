from django.contrib import admin

# Register your models here.
from .models import ChatRoom, ChatMessage, PrivateChatRoom

admin.site.register(ChatRoom)
admin.site.register(PrivateChatRoom)
admin.site.register(ChatMessage)
