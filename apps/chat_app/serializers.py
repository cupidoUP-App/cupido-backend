"""Serializers para el sistema de chat.

- ContactoChatSerializer: datos del otro usuario en el chat
- UltimoMensajeSerializer: resumen del último mensaje
- ChatListSerializer: serializer principal de la lista de chats
"""

from rest_framework import serializers
from .models import Chat, Mensaje
from django.contrib.auth import get_user_model

User = get_user_model()


class ContactoChatSerializer(serializers.ModelSerializer):
    """Representa al otro usuario en el chat.

    Incluye nombre, email, última conexión e imagen de perfil principal.
    """

    imagen_principal = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'nombres', 'apellidos', 'email', 'last_login', 'imagen_principal')

    def get_imagen_principal(self, obj):
        try:
            imagen = obj.imagenes.filter(es_principal=True).first()
            if imagen and imagen.imagen:
                return imagen.imagen.url
        except Exception:
            pass
        return None


class UltimoMensajeSerializer(serializers.ModelSerializer):
    """Resumen del último mensaje (contenido + fecha) para la lista de chats."""

    class Meta:
        model = Mensaje
        fields = ('contenido', 'fechaHora')


class ChatListSerializer(serializers.ModelSerializer):
    """Serializer principal de la lista de chats del usuario.

    Campos:
    - contacto: el otro usuario del match
    - ultimo_mensaje: resumen del último mensaje (anotado)
    - no_leidos: conteo de mensajes no leídos (anotado)
    """

    ultimo_mensaje = UltimoMensajeSerializer(source='latest_message_data', read_only=True)
    no_leidos = serializers.IntegerField(read_only=True)
    contacto = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'activo', 'contacto', 'ultimo_mensaje', 'no_leidos')

    def get_contacto(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        user = request.user
        match = obj.match
        contacto = match.usuarioB if match.usuarioA == user else match.usuarioA
        return ContactoChatSerializer(contacto).data