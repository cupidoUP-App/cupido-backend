"""Modelos del sistema de chat.

- Chat: sala de chat vinculada 1:1 con un Match
- Mensaje: mensaje individual dentro de un chat
"""

from django.db import models
from django.conf import settings
from apps.match_app.models import Match


class Chat(models.Model):
    """Sala de chat asociada a un Match.

    Se crea automáticamente mediante señal post_save de Match.
    Solo existe un chat por match (OneToOneField).
    Puede desactivarse sin eliminar el match.
    """

    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="chat")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Chat entre {self.match.usuarioA.nombres} y {self.match.usuarioB.nombres}"


class Mensaje(models.Model):
    """Mensaje individual dentro de un chat.

    Se ordena por fechaHora ascendente. El remitente puede ser
    null si el usuario se elimina (SET_NULL).
    """

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="mensajes", db_index=True)
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="mensajes_enviados", db_index=True
    )
    contenido = models.TextField()
    fechaHora = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['fechaHora']

    def __str__(self):
        return f"Mensaje de {self.remitente} en chat {self.chat.id}"