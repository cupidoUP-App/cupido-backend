"""Serializer básico del modelo Usuario.

Expone los campos principales del usuario en respuestas JSON.
Se usa en login, sesión y consulta de perfil.
"""

from rest_framework import serializers
from apps.auth_app.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializa datos básicos del usuario (id, nombres, apellidos, email)."""

    class Meta:
        model = Usuario
        fields = ["usuario_id", "nombres", "apellidos", "email"]
