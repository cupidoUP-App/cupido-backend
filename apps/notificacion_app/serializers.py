"""Serializer de notificaciones.

Expone tipo, mensaje, fecha, estado, y metadatos adicionales
como chat_id, from_user_id y usuario_match_id.
"""

from rest_framework import serializers
from .models import notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializa notificaciones con metadatos de origen y relación.

    Campos calculados:
    - chat_id: ID del chat relacionado (si aplica)
    - from_user_id: ID del usuario que originó el evento
    - usuario_match_id: ID del otro usuario (solo para notificaciones MATCH)
    """

    usuario_destino = serializers.StringRelatedField()
    chat_id = serializers.SerializerMethodField()
    from_user_id = serializers.SerializerMethodField()
    usuario_match_id = serializers.SerializerMethodField()

    class Meta:
        model = notificacion
        fields = ('id', 'tipo', 'mensaje', 'fecha_envio', 'estado', 'usuario_destino', 'chat_id', 'from_user_id', 'usuario_match_id')
        read_only_fields = ('id', 'fecha_envio', 'chat_id', 'from_user_id', 'usuario_match_id')

    def get_chat_id(self, obj):
        return obj.chat_relacionado_id if obj.chat_relacionado_id else None

    def get_from_user_id(self, obj):
        return obj.usuario_origen_id if obj.usuario_origen_id else None

    def get_usuario_match_id(self, obj):
        if obj.tipo == notificacion.EVENT_MATCH:
            return obj.usuario_origen_id
        return None
