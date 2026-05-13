"""Serializer de inicio de sesión.

Valida credenciales (email + contraseña), verifica estado de cuenta
y reCAPTCHA. Retorna el usuario validado para la generación de JWT.
"""

from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from apps.auth_app.models import Usuario


class LoginSerializer(serializers.Serializer):
    """Valida credenciales de inicio de sesión.

    Verifica existencia del usuario, estado de la cuenta
    (bloquea inactiva/reportada), y contraseña con hash.
    """

    email = serializers.EmailField()
    contrasena = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        contrasena = attrs.get("contrasena")

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"email": "Usuario no encontrado."})

        estadocuenta = user.estadocuenta
        if estadocuenta in ["-2", "-1"]:
            raise serializers.ValidationError(
                {"email": f"Cuenta {estadocuenta}. No se permite el acceso."}
            )
        elif estadocuenta not in ["0", "1", "2", "3"]:
            raise serializers.ValidationError({"email": "Estado de cuenta inválido."})

        if not check_password(contrasena, user.contrasena):
            raise serializers.ValidationError({"contrasena": "Contraseña incorrecta."})

        attrs["user"] = user
        attrs["estadocuenta"] = estadocuenta
        return attrs
