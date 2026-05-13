"""Configuración ASGI con soporte para Django Channels (WebSockets).

Combina HTTP (Django ASGI) con WebSockets (chat + notificaciones),
protegidos con JwtAuthMiddleware y AllowedHostsOriginValidator.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.chat_app.middleware import JwtAuthMiddleware
import apps.chat_app.routing
import apps.notificacion_app.routing

websocket_urlpatterns = (
    apps.chat_app.routing.websocket_urlpatterns +
    apps.notificacion_app.routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddleware(URLRouter(websocket_urlpatterns))
    ),
})
