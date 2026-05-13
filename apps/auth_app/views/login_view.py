import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.auth_app.serializers.login_serializer import LoginSerializer
from apps.auth_app.serializers.usuario_serializer import UsuarioSerializer
from apps.auth_app.utils.tokens import create_jwt_for_user
from apps.auth_app.models import Usuario

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    Endpoint de inicio de sesión.

    Valida credenciales (email + contraseña + reCAPTCHA), verifica
    el estado de la cuenta, invalida sesiones previas (single session),
    y devuelve tokens JWT (access + refresh) con datos del usuario.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("🧩 Intento de inicio de sesión recibido.")
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        estadocuenta = serializer.validated_data["estadocuenta"]
        logger.debug(f"Tipo de user recibido: {type(user)}")
        logger.debug(f"Estado de cuenta: {estadocuenta}")

        # El usuario ya es instancia de Usuario (hereda de AbstractUser)

        logger.info(f"✅ Usuario validado correctamente: {user.email} (ID {user.usuario_id})")

        # Single session: Invalidar todas las sesiones previas del usuario
        try:
            previous_tokens = OutstandingToken.objects.filter(user=user)
            previous_count = previous_tokens.count()
            for token in previous_tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            if previous_count > 0:
                logger.info(f"🔒 Invalidadas {previous_count} sesiones previas para {user.email}")
        except Exception as e:
            logger.warning(f"⚠️ Error al invalidar sesiones previas para {user.email}: {e}")

        # Generar tokens JWT
        try:
            tokens = create_jwt_for_user(user)
            logger.info(f"🎫 Tokens JWT generados para usuario {user.email}")
        except Exception as e:
            logger.error(f"🔥 Error al generar tokens JWT para {user.email}: {e}")
            return Response(
                {"error": "Error interno al generar el token de autenticación."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Actualizar último inicio de sesión (si aplica)
        if hasattr(user, "last_login"):
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])
            logger.debug(f"🕓 last_login actualizado para {user.email}")

        # Construir respuesta
        response_payload = {
            "user": UsuarioSerializer(user).data,
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "estadocuenta": estadocuenta,
        }

        logger.info(f"✅ Login exitoso para {user.email}")
        return Response(response_payload, status=status.HTTP_200_OK)