# apps/auth_app/views/register_view.py
#wertyujhbvcx
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings

from apps.auth_app.serializers.register_serializer import RegisterSerializer
from apps.auth_app.utils.redis_client import set_json
from apps.auth_app.utils import codes, email_utils

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    Paso 1 del registro de usuario.

    Recibe datos iniciales (email, contraseña, reCAPTCHA, T&C),
    los valida, los guarda temporalmente en Redis y envía un
    código de verificación por correo electrónico.

    No crea el usuario en BD hasta que se verifique el email
    (Paso 2 en VerifyEmailView).
    """

    throttle_scope = "verify_email"

    def post(self, request):
        logger.info("Iniciando proceso de registro.")
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logger.info("Datos del serializer validados correctamente.")

        email = serializer.validated_data["email"]
        logger.info(f"Email del usuario: {email}")

        # Verificar si ya existe un registro temporal previo (previene spam)
        redis_key_data = f"register:{email}"
        redis_key_code = f"verify:{email}"

        logger.info(f"Intentando guardar datos temporales en Redis con clave: {redis_key_data}")
        if set_json(redis_key_data, serializer.to_redis_payload(), ttl=600):
            logger.info("Datos temporales guardados en Redis exitosamente.")
            # Generar un nuevo código de verificación
            logger.info("Generando código de verificación.")
            verification_code = codes.generate_verification_code(email)
            logger.info(f"Código de verificación generado: {verification_code}")

            # Guardar código en Redis
            logger.info(f"Guardando código en Redis con clave: {redis_key_code}")
            set_json(redis_key_code, {"code": verification_code}, ttl=600)
            logger.info("Código guardado en Redis exitosamente.")

            # Enviar correo con el código
            logger.info(f"Enviando correo de verificación a: {email}")
            try:
                email_sent = email_utils.send_verification_email(email, verification_code)
                if email_sent:
                    logger.info("Correo de verificación enviado exitosamente.")
                else:
                    logger.error("Fallo al enviar correo de verificación.")
                    return Response(
                        {"error": "No se pudo enviar el correo de verificación."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            except Exception as e:
                logger.error(f"Excepción al enviar correo: {str(e)}")
                return Response(
                    {"error": f"No se pudo enviar el correo de verificación: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            logger.info("Proceso de registro completado exitosamente.")
            return Response(
                {
                    "message": "Datos registrados temporalmente. "
                               "Revisa tu correo para continuar el registro."
                },
                status=status.HTTP_200_OK,
            )
        else:
            logger.error("No se pudo guardar datos temporales en Redis.")
            return Response(
                {"error": "No se pudo almacenar la información temporalmente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

