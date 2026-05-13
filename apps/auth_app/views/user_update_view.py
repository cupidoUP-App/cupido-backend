# apps/auth_app/views/user_update_view.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_app.serializers.user_update_serializer import UserUpdateSerializer
from apps.auth_app.utils.user_update import get_user_update_response_data


class UserUpdateView(APIView):
    """
    Actualiza los datos del perfil del usuario autenticado.

    Acepta PATCH parcial con nombres, apellidos, género, fecha de
    nacimiento y descripción. Delega en get_user_update_response_data()
    para construir la respuesta estructurada.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user.refresh_from_db()

        response = get_user_update_response_data(user)
        return Response(response, status=status.HTTP_200_OK)


