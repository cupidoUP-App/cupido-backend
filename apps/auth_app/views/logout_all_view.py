# apps/auth_app/views/logout_all_view.py

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

logger = logging.getLogger(__name__)


class LogoutAllView(APIView):
    """
    Cierra sesión en todos los dispositivos simultáneamente.

    Busca y agrega a la blacklist TODOS los refresh tokens
    Outstanding asociados al usuario autenticado, forzando
    el cierre de sesión en todos los clientes/dispositivos.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        logger.info(f"🚪 Logout global solicitado por {user.email} (ID {user.pk})")

        try:
            tokens = OutstandingToken.objects.filter(user=user)
            total = tokens.count()

            for token in tokens:
                # Evita duplicar blacklist si ya lo está
                BlacklistedToken.objects.get_or_create(token=token)

            logger.info(f"🧹 {total} tokens revocados para {user.email}.")
            return Response(
                {"message": f"Sesiones cerradas en {total} dispositivos."},
                status=status.HTTP_205_RESET_CONTENT,
            )

        except Exception as e:
            logger.critical(f"🔥 Error durante logout global de {user.email}: {e}")
            return Response(
                {"error": "Error interno al cerrar todas las sesiones."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
