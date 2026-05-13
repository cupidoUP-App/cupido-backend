"""Serializer para reenvío de código de verificación.

Valida email institucional y verifica que no exista un usuario
ya registrado con ese correo.
"""

from rest_framework import serializers
from apps.auth_app.utils.validators import validate_institutional_email
from apps.auth_app.models import Usuario


class ResendCodeSerializer(serializers.Serializer):
    """Valida email para reenviar código de verificación.

    Previene reenvío si el usuario ya completó el registro.
    """

    email = serializers.EmailField()

    def validate_email(self, value):
        validate_institutional_email(value)
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "El correo ya está registrado. Usa iniciar sesión o recuperar contraseña."
            )
        return value
