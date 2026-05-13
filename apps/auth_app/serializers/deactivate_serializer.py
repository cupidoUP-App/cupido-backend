"""Serializer para desactivación de cuenta de usuario autenticado.

Realiza soft delete cambiando estadocuenta a 'Inactiva'.
Requiere contraseña actual y confirmación explícita.
"""

import logging
from django.contrib.auth.hashers import check_password
from rest_framework import serializers

logger = logging.getLogger(__name__)


class DeactivateAccountSerializer(serializers.Serializer):
    """Valida y ejecuta la desactivación de cuenta (soft delete).

    Requiere contraseña actual y palabra de confirmación.
    Cambia estadocuenta a 'Inactiva' sin eliminar datos.
    """

    contrasena = serializers.CharField(write_only=True)
    confirmacion = serializers.CharField(write_only=True)

    def validate_contrasena(self, value):
        """Verifica que la contraseña actual coincida."""
        user = self.context["request"].user
        if not check_password(value, user.contrasena):
            raise serializers.ValidationError("Contraseña incorrecta.")
        return value

    def validate_confirmacion(self, value):
        """Verifica que el usuario confirme explícitamente la desactivación."""
        if value.lower() not in ["desactivar", "confirmar", "si"]:
            raise serializers.ValidationError(
                "Debe escribir 'desactivar', 'confirmar' o 'si' para proceder."
            )
        return value

    def save(self):
        """Ejecuta el soft delete: cambia estadocuenta a 'Inactiva'."""
        user = self.context["request"].user
        user.estadocuenta = "Inactiva"
        user.save(update_fields=["estadocuenta"])
        return user