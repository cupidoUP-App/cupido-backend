# apps/auth_app/views/user_get_view.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_app.utils.user_get import get_user_profile_data


class UserGetView(APIView):
    """
    Obtiene todos los datos del perfil del usuario autenticado.

    Delega en get_user_profile_data() para construir la respuesta
    con los datos consolidados del usuario.
    """

    def get(self, request):
        user = request.user
        payload = get_user_profile_data(user)
        return Response(payload, status=status.HTTP_200_OK)

