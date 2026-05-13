# apps/auth_app/views/logout_view.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

logger = logging.getLogger(__name__)


class LogoutView(APIView):
    """
    Cierra sesión invalidando el refresh token actual.

    Recibe el refresh token en el body, lo agrega a la blacklist
    de SimpleJWT para que no pueda ser usado nuevamente.
    Requiere JWT access válido en header.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logger.info(f"🚪 Logout solicitado por usuario {request.user.email} (ID {request.user.pk}).")

        refresh_token = request.data.get("refresh")

        if not refresh_token:
            logger.warning("No se proporcionó refresh token para el logout.")
            return Response(
                {"error": "Debe enviar el refresh token para cerrar sesión."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # marca el token como inválido
            logger.info(f"✅ Refresh token invalidado correctamente para usuario {request.user.email}.")
            return Response(
                {"message": "Sesión cerrada exitosamente."},
                status=status.HTTP_205_RESET_CONTENT
            )

        except TokenError as e:
            logger.error(f"❌ Error al invalidar refresh token: {e}")
            return Response(
                {"error": "Token inválido o ya caducado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.critical(f"🔥 Error inesperado durante logout: {e}")
            return Response(
                {"error": "Error interno al cerrar sesión."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

