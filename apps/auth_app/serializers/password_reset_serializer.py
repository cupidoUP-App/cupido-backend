"""Serializers para recuperación de contraseña.

- PasswordResetRequestSerializer: solicita token por email
- PasswordResetConfirmSerializer: valida token y actualiza contraseña
"""

import logging
import uuid
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from apps.auth_app.models import Usuario

from apps.auth_app.utils.validators import validate_institutional_email
from apps.auth_app.utils.redis_client import set_json, get_json
from apps.auth_app.utils import email_utils

logger = logging.getLogger(__name__)

RESET_TOKEN_TTL = 1800


class PasswordResetRequestSerializer(serializers.Serializer):
    """Solicita token de recuperación. No revela si el email existe por seguridad."""

    email = serializers.EmailField()

    def validate_email(self, value):
        validate_institutional_email(value)
        return value

    def save(self):
        email = self.validated_data["email"]
        try:
            Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return

        reset_token = str(uuid.uuid4())
        set_json(f"reset_token:{reset_token}", {"email": email, "used": False}, ttl=RESET_TOKEN_TTL)

        reset_link = f"https://cupidocol.com/reset-password?token={reset_token}"
        try:
            email_utils.send_password_reset_email(email, reset_link)
        except Exception as e:
            logger.error(f"Error enviando email de recuperación a {email}: {e}")


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Valida token UUID y actualiza la contraseña del usuario.

    Token: UUID de 36 caracteres almacenado en Redis con TTL de 30 min.
    """

    token = serializers.CharField(min_length=36, max_length=36)
    nueva_contrasena = serializers.CharField(write_only=True, min_length=8)

    def validate_nueva_contrasena(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        token = attrs.get("token")
        redis_key = f"reset_token:{token}"
        reset_data = get_json(redis_key)
        if not reset_data:
            raise serializers.ValidationError({"token": "Token expirado o inválido."})
        if reset_data.get("used", False):
            raise serializers.ValidationError({"token": "Token ya utilizado."})

        email = reset_data.get("email")
        if not email:
            raise serializers.ValidationError({"token": "Token inválido."})

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"token": "Usuario no encontrado."})

        attrs["user"] = user
        attrs["token_key"] = redis_key
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.contrasena = make_password(self.validated_data["nueva_contrasena"])
        user.save(update_fields=["contrasena"])

        reset_data = get_json(self.validated_data["token_key"])
        if reset_data:
            reset_data["used"] = True
            set_json(self.validated_data["token_key"], reset_data, ttl=RESET_TOKEN_TTL)
        return user
