"""Señales del módulo de Match.

Crea automáticamente un Chat cuando se genera un nuevo Match mutuo,
completando el flujo: Like → Match → Chat.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models import Match

logger = logging.getLogger(__name__)

try:
    from apps.chat_app.models import Chat
except ImportError:
    Chat = None


@receiver(post_save, sender=Match)
def crear_chat_automatico(sender, instance, created, **kwargs):
    """Crea un Chat automáticamente al crearse un Match.

    Flujo completo: UsuarioA LIKE UsuarioB → Match mutuo → Chat creado.

    El Chat es necesario para que los usuarios puedan intercambiar mensajes
    después de un match exitoso.
    """
    if not created or Chat is None:
        return

    if hasattr(instance, 'chat'):
        return

    try:
        chat = Chat.objects.create(match=instance, activo=True)
        logger.info(f"Chat id={chat.id} creado para Match id={instance.id}")
    except Exception as e:
        logger.error(f"Error al crear Chat automático: {e}")
