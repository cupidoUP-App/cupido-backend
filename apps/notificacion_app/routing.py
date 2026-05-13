"""Enrutamiento WebSocket para notificaciones.

Define el patrón: ws/notificaciones/<user_id>/
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/notificaciones/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
]
