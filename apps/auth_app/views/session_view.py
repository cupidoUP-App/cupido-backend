from apps.auth_app.serializers.session_serializer import SessionSerializer
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
import logging

from apps.auth_app.serializers.usuario_serializer import UsuarioSerializer  # sigue siendo necesario

logger = logging.getLogger(__name__)


class SessionInfoView(APIView):
    """
    Devuelve información del usuario autenticado.

    Utiliza SessionSerializer para estructurar los datos de sesión
    incluyendo datos del usuario, estado de cuenta y perfil.
    Requiere JWT válido en header Authorization.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user or not user.is_authenticated:
            logger.warning("Intento de acceso sin autenticación a /session/")
            return Response(
                {"error": "Autenticación requerida."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        logger.info(f"📡 Consultando sesión activa para usuario {user.email} (ID {user.pk})")

        session_data = {
            "message": "Sesión activa.",
            "user": user,
        }

        serializer = SessionSerializer(session_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


