"""
Chat WebSocket consumer.

Maneja la conexión en tiempo real para el envío y recepción de mensajes.
Autentica mediante JwtAuthMiddleware, persiste mensajes en BD y
transmite a todos los miembros del chat vía channel layer.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Mensaje


@database_sync_to_async
def save_message(chat_id, user, message_content):
    """Persiste un mensaje en la BD validando que el usuario pertenezca al chat.

    Args:
        chat_id: ID del chat.
        user: Usuario autenticado que envía el mensaje.
        message_content: Contenido del mensaje.

    Returns:
        Mensaje si se guardó correctamente, None si el usuario no pertenece al chat.
    """
    try:
        chat_obj = Chat.objects.get(id=chat_id)
        if chat_obj.match.usuarioA != user and chat_obj.match.usuarioB != user:
            return None
        return Mensaje.objects.create(chat=chat_obj, remitente=user, contenido=message_content)
    except Chat.DoesNotExist:
        return None


@database_sync_to_async
def touch_user_last_login(user):
    """Actualiza last_login del usuario como aproximación de 'última vez en línea'."""
    try:
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
    except Exception:
        pass


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket para chat en tiempo real.

    Usa autenticación JWT (vía JwtAuthMiddleware en la query string).
    Los mensajes se persisten en BD y se transmiten a todos los
    participantes mediante el group_name 'chat_{chat_id}'.
    """

    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close(code=4003)
            return

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        await touch_user_last_login(self.user)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if not self.user.is_anonymous:
            await touch_user_last_login(self.user)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if self.user.is_anonymous:
            return

        mensaje_obj = await save_message(self.chat_id, self.user, message)
        if mensaje_obj:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_data': {
                        'id': mensaje_obj.id,
                        'contenido': mensaje_obj.contenido,
                        'remitente_email': self.user.email,
                        'es_mio': True,
                        'fecha': mensaje_obj.fechaHora.strftime("%Y-%m-%d %H:%M:%S"),
                        'leido': False,
                    }
                }
            )

    async def chat_message(self, event):
        message_data = event['message_data']
        message_data['es_mio'] = (self.user.email == message_data['remitente_email'])
        await self.send(text_data=json.dumps({'message': message_data}))