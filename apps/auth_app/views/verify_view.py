# apps/auth_app/views/verify_view.py
import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.auth_app.models import Usuario
from apps.auth_app.serializers.verify_serializer import VerifyEmailSerializer
# UsuarioProxy eliminado, ahora usamos Usuario directamente
from apps.auth_app.utils.redis_client import delete_key
from apps.auth_app.utils import codes

from rest_framework_simplejwt.tokens import RefreshToken
from apps.match_app.models import Match

logger = logging.getLogger(__name__)


class VerifyEmailView(APIView):
    """
    Paso 2 del registro de usuario.

    Verifica el código enviado por email, recupera los datos
    temporales desde Redis, crea el usuario definitivo en BD,
    genera un match de bienvenida con el admin (ID 1), y
    devuelve tokens JWT para iniciar sesión automáticamente.
    """

    throttle_scope = "verify_email"

    @transaction.atomic
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Obtener los datos que fueron guardados temporalmente en Redis
        registration_payload = serializer.get_registration_payload()

        try:
            # Crear usuario en la base de datos con datos mínimos del registro y dummies para los demás
            user = Usuario.objects.create(
                nombres="Dummy",  # Valor dummy
                apellidos="Dummy",  # Valor dummy
                email=email,
                password=registration_payload.get("password"),  # ya hasheada
                numerotelefono="0000000000",  # Valor dummy
                tyc=registration_payload.get("tyc", True),
                firma=registration_payload.get("firma"),
                estadocuenta=registration_payload.get("estadocuenta", "1"),
                fecharegistro=registration_payload.get("fecharegistro"),
                fechanacimiento="2000-01-01",  # Valor dummy,
                username = email,
            )
        except Exception as e:
            return Response(
                {"error": f"No se pudo crear el usuario: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Eliminar datos temporales del registro y el código
        delete_key(f"register:{email}")
        codes.invalidate_code(email)

        # Crear Match de bienvenida con usuario ID 1 para chat automático
        try:
            admin_user = Usuario.objects.filter(usuario_id=1).first()
            if admin_user and user.usuario_id != 1:
                # Ordenar IDs para unicidad (constraint unique_together)
                user_a_id = min(user.usuario_id, admin_user.usuario_id)
                user_b_id = max(user.usuario_id, admin_user.usuario_id)
                user_a = Usuario.objects.get(usuario_id=user_a_id)
                user_b = Usuario.objects.get(usuario_id=user_b_id)
                
                Match.objects.get_or_create(
                    usuarioA=user_a,
                    usuarioB=user_b,
                    defaults={'estadoMatch': 'ACTIVO'}
                )
                logger.info(f"Match de bienvenida creado para usuario {user.usuario_id} con usuario ID 1")
        except Exception as e:
            logger.warning(f"No se pudo crear match de bienvenida: {e}")

        # Generar tokens JWT (opcional)
        try:
            refresh = RefreshToken.for_user(user)
            tokens = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        except Exception as e:
            tokens = None

        return Response(
            {
                "message": "Cuenta verificada y creada exitosamente.",
                "user": {
                    "usuario_id": user.usuario_id,
                    "nombres": user.nombres,
                    "email": user.email,
                    "estadocuenta": user.estadocuenta,
                },
                **({"tokens": tokens} if tokens else {}),
            },
            status=status.HTTP_201_CREATED,
        )
