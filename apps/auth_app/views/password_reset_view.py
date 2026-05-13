# apps/auth_app/views/password_reset_view.py
"""
Vistas para recuperación de contraseña.
- PasswordResetRequestView: Solicita recuperación enviando email con token
- PasswordResetConfirmView: Confirma recuperación con token y nueva contraseña
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from apps.auth_app.serializers.password_reset_serializer import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

logger = logging.getLogger(__name__)


class PasswordResetRequestView(APIView):
    """
    Solicita restablecimiento de contraseña.

    Recibe email institucional, genera un token UUID único,
    lo guarda en Redis con TTL de 30 min, y envía un enlace
    de recuperación por correo. Siempre responde OK por seguridad
    (no revela si el email existe en el sistema).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logger.info("🛠️ Solicitud de recuperación de contraseña recibida.")
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Procesar solicitud (siempre OK por seguridad)
        serializer.save()

        logger.info("✅ Solicitud de recuperación procesada.")
        return Response(
            {"message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    Confirma el restablecimiento de contraseña con el token.

    Valida el token UUID contra Redis, verifica que no haya sido
    usado previamente, y actualiza la contraseña del usuario
    aplicando los validadores de seguridad de Django.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        logger.info("🔐 Confirmación de recuperación de contraseña recibida.")
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Actualizar contraseña
        user = serializer.save()

        logger.info(f"✅ Contraseña restablecida para usuario {user.email}")
        return Response(
            {"message": "Contraseña restablecida correctamente."},
            status=status.HTTP_200_OK
        )
