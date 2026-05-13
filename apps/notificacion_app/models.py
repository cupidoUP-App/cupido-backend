"""Modelo de notificaciones del sistema (like, match, chat).

Se crean mediante señales Django y se envían en tiempo real
al usuario destino vía WebSocket (Django Channels).
"""

from django.db import models
from django.conf import settings


class notificacion(models.Model):
    """Notificación push para eventos de like, match y chat.

    Se crea automáticamente mediante señales en notificacion_app/signals.py
    y se envía al WebSocket del usuario destino en tiempo real.
    """

    EVENT_LIKE = 'like'
    EVENT_MATCH = 'match'
    EVENT_CHAT = 'chat'
    EVENT_REPORT = "Reporte"
    EVENT_CHOICES = [
        (EVENT_LIKE, 'Like'), (EVENT_MATCH, 'Match'), (EVENT_CHAT, "Chat"), (EVENT_REPORT, "Reporte"),
    ]

    STATUS_PENDING = 'pendiente'
    STATUS_SENT = 'enviado'
    STATUS_READ = 'leido'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'), (STATUS_SENT, 'Enviado'), (STATUS_READ, 'Leido'),
    ]

    tipo = models.CharField(max_length=20, choices=EVENT_CHOICES)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    usuario_destino = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    chat_relacionado = models.ForeignKey('chat_app.Chat', on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones')
    usuario_origen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='notificaciones_enviadas')

    class Meta:
        db_table = 'notificacion'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f"Notificacion(to={self.usuario_destino.username}, tipo={self.tipo})"

