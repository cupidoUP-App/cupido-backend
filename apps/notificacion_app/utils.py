"""Utilidad para enviar eventos en tiempo real a grupos WebSocket.

Usa Django Channels channel layer para transmitir notificaciones
a los usuarios conectados por WebSocket.
"""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def enviar_a_grupo(nombre_grupo: str, tipo_evento: str, data: dict):
    """Envía un evento a un grupo WebSocket de Django Channels.

    Args:
        nombre_grupo: Nombre del grupo (ej: "user_123").
        tipo_evento: Nombre del método en el consumer (ej: "notification_message").
        data: Payload del evento.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        nombre_grupo,
        {"type": tipo_evento, "data": data}
    )
