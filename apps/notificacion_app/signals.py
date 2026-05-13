"""Señales Django que generan notificaciones en tiempo real.

Tres señales principales:
1. LIKE: Cuando un usuario recibe un Like (post_save DetallesLike)
2. MATCH: Cuando se crea un Chat (que implica un Match mutuo)
3. CHAT: Cuando se recibe un mensaje y el chat no está abierto

Cada señal crea un registro en notificacion y envía el evento
al WebSocket del usuario destino via enviar_a_grupo().
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.cache import cache
import logging

from .models import notificacion
from .utils import enviar_a_grupo

logger = logging.getLogger(__name__)

# ================================
# IMPORTS EXTERNOS (otras apps)
# ================================
try:
    from apps.like_app.models import DetallesLike
except ImportError:
    DetallesLike = None

try:
    from match.models import Match
except ImportError:
    Match = None

try:
    from apps.chat_app.models import Mensaje, Chat
except ImportError:
    Mensaje = None
    Chat = None


# --------------------------------------------------------
# NOTIFICACIÓN POR LIKE
# --------------------------------------------------------
if DetallesLike is not None:
    @receiver(post_save, sender=DetallesLike)
    def crear_notificacion_desde_like(sender, instance, created, **kwargs):
        if not created:
            return
        
        # Solo notificar si es un LIKE positivo
        if instance.estado != 'LIKE':
            return

        usuario_emisor = getattr(instance, 'usuarioEmisor', None)
        usuario_receptor = getattr(instance, 'usuarioReceptor', None)

        if usuario_receptor is None or usuario_emisor is None:
            return

        nombre_emisor = getattr(usuario_emisor, 'nombres', 'Alguien')
        mensaje = f"{nombre_emisor} te dio like"

        notif = notificacion.objects.create(
            tipo=notificacion.EVENT_LIKE,
            mensaje=mensaje,
            usuario_destino=usuario_receptor,
            usuario_origen=usuario_emisor,
        )

        payload = {
            "id": notif.id,
            "tipo": notif.tipo,
            "mensaje": notif.mensaje,
            "fecha_envio": notif.fecha_envio.isoformat(),

            "from_user_id": usuario_emisor.id,
            "from_username": usuario_emisor.username,
        }

        transaction.on_commit(
            lambda: enviar_a_grupo(
                f"user_{usuario_receptor.id}",
                "notification_message",
                payload
            )
        )


# --------------------------------------------------------
# NOTIFICACIÓN POR MATCH
# --------------------------------------------------------
if Chat is not None:
    @receiver(post_save, sender=Chat)
    def crear_notificacion_desde_chat_match(sender, instance, created, **kwargs):
        if not created:
            return

        logger.info(f"Signal MATCH (via Chat) activado para Chat id={instance.id}")

        # El 'instance' ahora es el Chat
        chat = instance
        match = chat.match
        
        user_a = match.usuarioA
        user_b = match.usuarioB

        # Excluir notificaciones para match de bienvenida con usuario ID 1
        WELCOME_USER_ID = 1
        if user_a.id == WELCOME_USER_ID or user_b.id == WELCOME_USER_ID:
            logger.info(f"Ignorando notificación de match de bienvenida con usuario ID {WELCOME_USER_ID}")
            return

        # Ya tenemos el chat, es 'instance'
        chat_id = chat.id

        # Notificación para usuario A
        try:
            mensaje_a = (
                f"Match! Tienes un nuevo match con "
                f"{getattr(user_b, 'nombres', user_b.username)}"
            )

            notif_a = notificacion.objects.create(
                tipo=notificacion.EVENT_MATCH,
                mensaje=mensaje_a,
                usuario_destino=user_a,
                usuario_origen=user_b,
                chat_relacionado=chat
            )

            payload_a = {
                "id": notif_a.id,
                "tipo": notif_a.tipo,
                "mensaje": notif_a.mensaje,
                "fecha_envio": notif_a.fecha_envio.isoformat(),
                "usuario_match_id": user_b.id,
                "chat_id": chat_id,
            }

            transaction.on_commit(
                lambda: enviar_a_grupo(
                    f"user_{user_a.id}",
                    "notification_message",
                    payload_a
                )
            )

        except Exception as e:
            logger.error(f"Error creando notificación MATCH para usuario A: {e}")

        # Notificación para usuario B
        try:
            mensaje_b = (
                f"Match! Tienes un nuevo match con "
                f"{getattr(user_a, 'nombres', user_a.username)}"
            )

            notif_b = notificacion.objects.create(
                tipo=notificacion.EVENT_MATCH,
                mensaje=mensaje_b,
                usuario_destino=user_b,
                usuario_origen=user_a,
                chat_relacionado=chat
            )

            payload_b = {
                "id": notif_b.id,
                "tipo": notif_b.tipo,
                "mensaje": notif_b.mensaje,
                "fecha_envio": notif_b.fecha_envio.isoformat(),
                "usuario_match_id": user_a.id,
                "chat_id": chat_id,
            }

            transaction.on_commit(
                lambda: enviar_a_grupo(
                    f"user_{user_b.id}",
                    "notification_message",
                    payload_b
                )
            )

        except Exception as e:
            logger.error(f"Error creando notificación MATCH para usuario B: {e}")


# --------------------------------------------------------
# NOTIFICACIÓN POR NUEVO MENSAJE DE CHAT
# --------------------------------------------------------
if Mensaje is not None:
    @receiver(post_save, sender=Mensaje)
    def notificar_mensaje_chat(sender, instance, created, **kwargs):
        if not created:
            return

        mensaje = instance
        chat = mensaje.chat
        remitente = mensaje.remitente

        usuarioA = chat.match.usuarioA
        usuarioB = chat.match.usuarioB

        receptor = usuarioB if remitente == usuarioA else usuarioA

        if receptor is None:
            return

        cache_key = f"chat_abierto_usuario_{receptor.id}"
        chat_abierto_id = cache.get(cache_key)

        if chat_abierto_id == chat.id:
            return

        texto = f"{remitente.nombres} te envió un mensaje"
        notif = notificacion.objects.create(
            tipo=notificacion.EVENT_CHAT,
            mensaje=texto,
            usuario_destino=receptor
        )

        payload = {
            "id": notif.id,
            "tipo": notif.tipo,
            "mensaje": notif.mensaje,
            "fecha_envio": notif.fecha_envio.isoformat(),
            "chat_id": chat.id,
        }

        transaction.on_commit(
            lambda: enviar_a_grupo(
                f"user_{receptor.id}",
                "notification_message",
                payload
            )
        )
