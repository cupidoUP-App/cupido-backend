"""Vistas del módulo de perfiles de usuario.

- ProfileUpdateView: ver/editar perfil propio
- PerfilDetailView: ver perfil de otro usuario
- PerfilAdminUpdateView: admin edita perfil
- ProgramaViewSet: catálogo de programas académicos
- UbicacionViewSet: catálogo de ubicaciones
"""

from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from apps.profile_app.subapps.profile.models import Perfil
from apps.profile_app.subapps.profile.serializer import *
from apps.profile_app.subapps.profile.utils import get_or_create_user_profile


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """Permite al usuario autenticado obtener o actualizar su propio perfil.

    GET: Obtiene el perfil. Lo crea automáticamente si no existe.
    PATCH: Actualiza campos parcialmente.
    """

    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_or_create_user_profile(self.request.user)

    def patch(self, request, *args, **kwargs):
        perfil = self.get_object()
        serializer = self.get_serializer(perfil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        perfil = self.get_object()
        return Response(self.get_serializer(perfil).data, status=status.HTTP_200_OK)


class PerfilDetailView(generics.RetrieveAPIView):
    """Obtiene perfil de otro usuario por ID (usuario_id o perfil_id).

    Incluye datos del perfil, usuario e imágenes asociadas.
    """

    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            return Perfil.objects.get(usuario__usuario_id=pk)
        except (Perfil.DoesNotExist, ValueError):
            return super().get_object()

    def get(self, request, *args, **kwargs):
        perfil = self.get_object()
        perfil_data = self.get_serializer(perfil).data

        usuario = perfil.usuario
        user_data = None
        imagenes_data = []
        if usuario:
            from apps.auth_app.serializers.user_get_serializer import UserGetSerializer
            user_data = UserGetSerializer(usuario).data
            from apps.profile_app.subapps.imageUpload.models import Imagen
            from apps.profile_app.subapps.imageUpload.serializers import ImagenSerializer
            imagenes_data = ImagenSerializer(Imagen.objects.filter(usuario=usuario), many=True).data

        return Response({**perfil_data, "usuario": user_data, "images": imagenes_data}, status=status.HTTP_200_OK)


class PerfilAdminUpdateView(generics.RetrieveUpdateAPIView):
    """Permite a un administrador ver o actualizar cualquier perfil por ID."""

    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer
    permission_classes = [permissions.AllowAny]


class ProgramaViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de programas académicos (solo lectura)."""
    queryset = Programa.objects.all()
    serializer_class = ProgramaSerializer


class UbicacionViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de ubicaciones (solo lectura)."""
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer