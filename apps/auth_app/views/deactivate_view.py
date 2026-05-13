# apps/auth_app/views/deactivate_view.py
"""
Vista para desactivación de cuenta de usuario autenticado.
Realiza soft delete cambiando estadocuenta a 'Inactiva'.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from apps.auth_app.serializers.deactivate_serializer import DeactivateAccountSerializer

logger = logging.getLogger(__name__)


class DeactivateAccountView(APIView):
    """
    Desactiva la cuenta del usuario autenticado (soft delete).

    Requiere contraseña actual (verificación de identidad) y
    confirmación explícita. Cambia estadocuenta a 'Inactiva'
    sin eliminar datos del usuario.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logger.info(f"🚫 Solicitud de desactivación de cuenta para {request.user.email}")
        serializer = DeactivateAccountSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Desactivar cuenta
        serializer.save()

        logger.info(f"✅ Cuenta desactivada exitosamente para {request.user.email}")
        return Response(
            {"message": "Cuenta desactivada correctamente. Puedes reactivarla contactando al soporte."},
            status=status.HTTP_200_OK
        )
