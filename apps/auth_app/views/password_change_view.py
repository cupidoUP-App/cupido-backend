# apps/auth_app/views/password_change_view.py
"""
Vista para cambio de contraseña de usuario autenticado.
Requiere contraseña actual y nueva contraseña válida.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from apps.auth_app.serializers.password_change_serializer import PasswordChangeSerializer

logger = logging.getLogger(__name__)


class PasswordChangeView(APIView):
    """
    Permite al usuario autenticado cambiar su contraseña.

    Requiere contraseña actual (para verificación de identidad)
    y nueva contraseña (con validaciones de seguridad de Django).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logger.info(f"🔑 Solicitud de cambio de contraseña para usuario {request.user.email}")
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Cambiar contraseña
        serializer.save()

        logger.info(f"✅ Contraseña cambiada exitosamente para {request.user.email}")
        return Response(
            {"message": "Contraseña cambiada exitosamente."},
            status=status.HTTP_200_OK
        )
