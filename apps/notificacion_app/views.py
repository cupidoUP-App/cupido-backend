"""ViewSet para gestión de notificaciones push.

CRUD básico (restringido al usuario autenticado) más acciones
personalizadas: mark_read, chat_abierto, chat_cerrado.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.cache import cache
from .models import notificacion
from .serializers import NotificacionSerializer


class NotificacionViewSet(viewsets.ModelViewSet):
    """CRUD de notificaciones del usuario autenticado.

    Acciones personalizadas:
    - POST /{id}/mark_read/ -> marca como leída
    - POST /chat_abierto/ -> suspende notificaciones del chat
    - POST /chat_cerrado/ -> reanuda notificaciones del chat
    """

    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return notificacion.objects.filter(usuario_destino=self.request.user).order_by('-fecha_envio')

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """Marca una notificación como leída (idempotente)."""
        try:
            instance = self.get_object()
        except Exception:
            return Response({"detail": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if instance.usuario_destino != request.user:
            return Response({"detail": "No tienes permiso para modificar esta notificación."}, status=status.HTTP_403_FORBIDDEN)

        if instance.estado == notificacion.STATUS_READ:
            return Response(self.get_serializer(instance).data)

        with transaction.atomic():
            instance.estado = notificacion.STATUS_READ
            instance.save(update_fields=['estado'])

        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['post'], url_path='chat_abierto')
    def chat_abierto(self, request):
        """Marca que el usuario abrió un chat (suspende notificaciones por 30 min)."""
        chat_id = request.data.get("chat_id")
        if not chat_id:
            return Response({"detail": "chat_id es requerido"}, status=400)
        cache.set(f"chat_abierto_usuario_{request.user.id}", chat_id, 60 * 30)
        return Response({"detail": "chat marcado como abierto"})

    @action(detail=False, methods=['post'], url_path='chat_cerrado')
    def chat_cerrado(self, request):
        """Reanuda notificaciones del chat."""
        cache.delete(f"chat_abierto_usuario_{request.user.id}")
        return Response({"detail": "chat cerrado"})
