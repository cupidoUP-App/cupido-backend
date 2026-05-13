"""Serializer del primer paso del registro de usuario.

Valida datos iniciales (reCAPTCHA, email institucional, contraseña, T&C),
NO crea el usuario en BD. Prepara un payload limpio para almacenar
temporalmente en Redis hasta la verificación del email.
"""

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.utils import timezone

from apps.auth_app.models import Usuario
from apps.auth_app.utils.recaptcha import verify_recaptcha_token
from apps.auth_app.utils.validators import validate_institutional_email


class RegisterSerializer(serializers.Serializer):
    """Valida datos del registro inicial y prepara payload para Redis.

    Campos: email (institucional), contrasena, recaptcha_token, tyc, firma.
    La contraseña se hashea con make_password antes de almacenar.
    """

    recaptcha_token = serializers.CharField(write_only=True, required=True, allow_blank=False)
    email = serializers.EmailField()
    contrasena = serializers.CharField(write_only=True, min_length=8)
    tyc = serializers.BooleanField()
    firma = serializers.CharField(required=True, allow_blank=False)

    def validate_recaptcha_token(self, value):
        """Verifica el token reCAPTCHA con Google. Maneja tokens expirados."""
        try:
            success, details = verify_recaptcha_token(value)
            if not success:
                error_codes = details.get("error-codes", [])
                if "timeout-or-duplicate" in error_codes:
                    raise serializers.ValidationError(
                        "El reCAPTCHA ha expirado. Por favor, completa el reCAPTCHA nuevamente."
                    )
                raise serializers.ValidationError(f"reCAPTCHA inválido. Códigos: {error_codes}")
            return value
        except RuntimeError as e:
            raise serializers.ValidationError(str(e))

    def validate_email(self, value):
        """Valida dominio @unipamplona.edu.co y verifica unicidad en BD."""
        validate_institutional_email(value)
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("El correo ya se encuentra registrado.")
        return value

    def validate_contrasena(self, value):
        """Aplica validadores de seguridad de Django a la contraseña."""
        validate_password(value)
        return value

    def validate(self, attrs):
        """Establece valores por defecto: estadocuenta=1, fecharegistro=now."""
        attrs["estadocuenta"] = "1"
        attrs["fecharegistro"] = timezone.now()
        attrs.pop("recaptcha_token", None)
        return attrs

    def to_redis_payload(self):
        """Prepara el dict para guardar en Redis. Hashea la contraseña.

        Returns:
            dict con datos validados listos para Redis.
            La contraseña se almacena hasheada (make_password).
        """
        if not hasattr(self, "validated_data"):
            raise RuntimeError("Debe llamar is_valid() antes de to_redis_payload().")

        data = dict(self.validated_data)
        raw_pass = data.pop("contrasena", None)
        if raw_pass:
            data["password"] = make_password(raw_pass)
        data["_from_registration"] = True
        return data