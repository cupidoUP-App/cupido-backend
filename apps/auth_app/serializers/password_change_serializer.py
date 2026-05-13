"""Serializer para cambio de contraseña de usuario autenticado.

Requiere contraseña actual (verificación de identidad) y nueva
contraseña con validaciones de seguridad de Django.
"""

import logging
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

logger = logging.getLogger(__name__)


class PasswordChangeSerializer(serializers.Serializer):
    """Valida y cambia la contraseña del usuario autenticado.

    Aplica validadores de Django (longitud, similitud, etc.) y
    verifica que la nueva contraseña sea diferente a la actual.
    """

    contrasena_actual = serializers.CharField(write_only=True)
    nueva_contrasena = serializers.CharField(write_only=True, min_length=8)

    def validate_nueva_contrasena(self, value):
        """Aplica validadores de seguridad de Django a la nueva contraseña."""
        validate_password(value)
        return value

    def validate_contrasena_actual(self, value):
        """Verifica que la contraseña actual coincida con la almacenada."""
        user = self.context["request"].user
        if not check_password(value, user.contrasena):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def validate(self, attrs):
        if attrs.get("contrasena_actual") == attrs.get("nueva_contrasena"):
            raise serializers.ValidationError(
                {"nueva_contrasena": "La nueva contraseña debe ser diferente a la actual."}
            )
        return attrs

    def save(self):
        """Hashea y actualiza la contraseña en la base de datos."""
        user = self.context["request"].user
        user.contrasena = make_password(self.validated_data["nueva_contrasena"])
        user.save(update_fields=["contrasena"])
        return user