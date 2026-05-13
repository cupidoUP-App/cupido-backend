"""Serializer de información de sesión activa.

Combina un mensaje de estado con los datos del usuario serializados.
Preparado para extenderse con metadatos de sesión (IP, expiración, etc.).
"""

from rest_framework import serializers
from apps.auth_app.serializers.usuario_serializer import UsuarioSerializer


class SessionSerializer(serializers.Serializer):
    """Serializa la sesión activa del usuario autenticado."""

    message = serializers.CharField(default="Sesión activa.")
    user = UsuarioSerializer()
