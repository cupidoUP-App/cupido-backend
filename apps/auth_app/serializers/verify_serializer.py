"""Serializer del segundo paso del registro (verificación de email).

Valida email institucional, código de 6 dígitos, existencia de registro
temporal en Redis, y expone get_registration_payload() para crear el usuario.
"""

from rest_framework import serializers

from apps.auth_app.utils.validators import validate_institutional_email
from apps.auth_app.utils import codes
from apps.auth_app.utils.redis_client import get_json


class VerifyEmailSerializer(serializers.Serializer):
    """Valida email + código OTP para completar el registro.

    Usa codes.verify_code() para validar contra Redis.
    Expone get_registration_payload() para recuperar los datos
    temporales del registro después de validar.
    """

    email = serializers.EmailField()
    codigo = serializers.CharField(write_only=True, min_length=6, max_length=10)

    def validate_email(self, value):
        """Valida formato de email institucional."""
        validate_institutional_email(value)
        return value

    def validate_codigo(self, value):
        """Normaliza y valida que el código sea numérico de al menos 4 dígitos."""
        code = value.strip()
        if not code.isdigit():
            raise serializers.ValidationError("El código de verificación debe ser numérico.")
        if len(code) < 4:
            raise serializers.ValidationError("Código de verificación demasiado corto.")
        return code

    def validate(self, attrs):
        """Verifica registro temporal en Redis y código OTP.

        Raises:
            ValidationError: si no hay registro previo o código inválido.
        """
        email = attrs.get("email")
        codigo = attrs.get("codigo")

        registration_payload = get_json(f"register:{email}")
        if not registration_payload:
            raise serializers.ValidationError({
                "email": "No existe un registro previo para este correo o ha expirado."
            })

        valid = codes.verify_code(email, codigo)
        if not valid:
            raise serializers.ValidationError({"codigo": "Código inválido o ha expirado."})

        self._registration_payload = registration_payload
        return attrs

    def get_registration_payload(self) -> dict:
        """Retorna los datos temporales del registro desde Redis.

        Debe llamarse después de is_valid() exitoso.
        """
        if not hasattr(self, "_registration_payload"):
            raise RuntimeError("Llama a is_valid() antes de usar get_registration_payload().")
        return dict(self._registration_payload)
