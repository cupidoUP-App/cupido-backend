"""Enrutamiento WebSocket para el chat.

Define el patrón de URL para conexiones WebSocket de chat: ws/chat/<chat_id>/
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<chat_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
