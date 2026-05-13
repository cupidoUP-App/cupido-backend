# apps/auth_app/views/resend_view.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.auth_app.serializers.resend_serializer import ResendCodeSerializer
from apps.auth_app.utils.redis_client import get_json
from apps.auth_app.utils import codes, email_utils


class ResendVerificationCodeView(APIView):
    """
    Reenvía un nuevo código de verificación al email del usuario.

    Verifica que exista un registro temporal activo en Redis,
    genera un nuevo código de 6 dígitos (sobrescribe el anterior),
    y lo envía por correo electrónico.
    """

    throttle_scope = "verify_email"

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Comprobar que el usuario inició el registro y que hay datos temporales
        register_key = f"register:{email}"
        reg_payload = get_json(register_key)
        if not reg_payload:
            return Response(
                {"error": "No hay un proceso de registro activo para este correo. Inicia el registro nuevamente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generar nuevo código: esto sobrescribe el anterior y resetea attempts
        try:
            new_code = codes.generate_verification_code(email)
        except Exception as e:
            return Response(
                {"error": f"No se pudo generar el código de verificación: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Enviar correo con nuevo código
        try:
            email_utils.send_verification_email(email, new_code)
        except Exception as e:
            return Response(
                {"error": f"No se pudo enviar el código por correo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"message": "Se ha enviado un nuevo código de verificación."}, status=status.HTTP_200_OK)
