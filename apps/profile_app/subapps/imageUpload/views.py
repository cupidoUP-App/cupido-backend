"""Vistas del módulo de imágenes de perfil.

- ImagenListCreateView: listar/subir imágenes del usuario autenticado
- ImagenDetailView: CRUD de imagen específica
- ImagenStatusView: verificar estado de fotos del usuario
"""

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Imagen
from .serializers import ImagenSerializer
from django.conf import settings


class ImagenListCreateView(generics.ListCreateAPIView):
    """Lista o sube imágenes del usuario autenticado.

    POST: Sube una nueva imagen con compresión y moderación automática.
    Límite máximo de fotos configurable via PHOTO_MAX_FILES (default: 3).
    """

    queryset = Imagen.objects.all()
    serializer_class = ImagenSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        max_photos = getattr(settings, 'PHOTO_MAX_FILES', 3)
        current_count = Imagen.objects.filter(usuario=self.request.user).count()
        if current_count >= max_photos:
            raise ValidationError({'detail': f"Has alcanzado el máximo de {max_photos} imágenes permitidas."})
        serializer.save(usuario=self.request.user)


class ImagenDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Obtiene, actualiza o elimina una imagen específica del usuario autenticado."""

    queryset = Imagen.objects.all()
    serializer_class = ImagenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(usuario=self.request.user)


class ImagenStatusView(APIView):
    """Verifica el estado de fotos del usuario autenticado.

    GET -> { has_minimum, current_count, minimum_required, maximum_allowed, can_upload_more }
    """

    permission_classes = [IsAuthenticated]
    MINIMUM_PHOTOS = 1

    def get(self, request):
        current_count = Imagen.objects.filter(usuario=request.user).count()
        max_photos = getattr(settings, 'PHOTO_MAX_FILES', 3)
        
        return Response({
            'has_minimum': current_count >= self.MINIMUM_PHOTOS,
            'current_count': current_count,
            'minimum_required': self.MINIMUM_PHOTOS,
            'maximum_allowed': max_photos,
            'can_upload_more': current_count < max_photos,
        })
