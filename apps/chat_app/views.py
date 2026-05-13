"""Vistas REST del sistema de chat.

Provee endpoints para lista de chats, historial de mensajes,
envío de mensajes (fallback REST), vaciar chat, y control
de estado "chat abierto" (para notificaciones).
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Q, F, Subquery, OuterRef, Count, Value
from django.utils import timezone
from django.db import models
from .models import Chat, Mensaje

from .serializers import ChatListSerializer

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# --- VISTA PARA OBTENER LA LISTA DE CHATS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_lista_chats(request):
    """Lista los chats activos del usuario con último mensaje y conteo de no leídos.

    Usa subqueries optimizadas y anotaciones para evitar N+1 queries.
    Incluye el contacto opuesto, último mensaje y cantidad de mensajes no leídos.
    """
    user = request.user

    ultimo_mensaje_subquery = Mensaje.objects.filter(
        chat=OuterRef('pk')
    ).order_by('-fechaHora').values('contenido', 'fechaHora')[:1]

    chats = Chat.objects.filter(activo=True).filter(
        Q(match__usuarioA=user) | Q(match__usuarioB=user)
    )

    chats_anotados = chats.annotate(
        no_leidos=Count(
            'mensajes',
            filter=Q(mensajes__leido=False) & ~Q(mensajes__remitente=user)
        ),
        latest_message_contenido=Subquery(ultimo_mensaje_subquery.values('contenido')),
        latest_message_fechaHora=Subquery(ultimo_mensaje_subquery.values('fechaHora')),
        latest_message_data=Value({}, output_field=models.JSONField())
    ).order_by(
        F('latest_message_fechaHora').desc(nulls_last=True)
    ).select_related('match__usuarioA', 'match__usuarioB')

    for chat in chats_anotados:
        if chat.latest_message_contenido:
            chat.latest_message_data = {
                'contenido': chat.latest_message_contenido,
                'fechaHora': chat.latest_message_fechaHora
            }
        else:
            chat.latest_message_data = None

    serializer = ChatListSerializer(chats_anotados, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_mensajes_chat(request, chat_id):
    """Obtiene todos los mensajes de un chat específico.

    Valida que el usuario pertenezca al chat, marca mensajes como
    leídos (excepto los propios), y retorna historial ordenado.
    """
    user = request.user
    try:
        chat = Chat.objects.select_related('match', 'match__usuarioA', 'match__usuarioB').get(
            id=chat_id, activo=True
        )

        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response({"error": "No tienes permiso para ver este chat."}, status=status.HTTP_403_FORBIDDEN)

        Mensaje.objects.filter(chat=chat, leido=False, remitente__isnull=False).exclude(
            remitente=user
        ).update(leido=True)

        mensajes = Mensaje.objects.select_related('remitente').filter(chat_id=chat.id).order_by('fechaHora')

        data = []
        for m in mensajes:
            try:
                remitente_email = m.remitente.email if m.remitente else "Sistema"
            except Exception:
                remitente_email = "Sistema"
            try:
                fecha_str = timezone.localtime(m.fechaHora).strftime("%Y-%m-%d %H:%M:%S") if m.fechaHora else ""
            except Exception:
                fecha_str = ""
            data.append({
                "id": m.id,
                "contenido": m.contenido,
                "remitente_email": remitente_email,
                "es_mio": m.remitente_id == user.id,
                "fecha": fecha_str,
                "leido": bool(getattr(m, "leido", False)),
            })

        return Response(data, status=status.HTTP_200_OK)

    except Chat.DoesNotExist:
        return Response({"error": "Chat no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error interno al cargar el historial del chat."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_mensaje(request, chat_id):
    """Endpoint REST para enviar mensajes (fallback cuando WebSocket no está disponible).

    Persiste el mensaje en BD y notifica al channel layer de Django Channels
    para que los usuarios conectados por WebSocket lo reciban en tiempo real.
    """
    user = request.user
    contenido = request.data.get('contenido', '').strip()
    if not contenido:
        return Response({"error": "El contenido del mensaje no puede estar vacío."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        chat = Chat.objects.select_related('match', 'match__usuarioA', 'match__usuarioB').get(id=chat_id, activo=True)

        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response({"error": "No tienes permiso para enviar mensajes en este chat."}, status=status.HTTP_403_FORBIDDEN)

        mensaje = Mensaje.objects.create(chat=chat, remitente=user, contenido=contenido)

        # Notificar por WebSocket a usuarios conectados
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{chat_id}',
                    {
                        'type': 'chat_message',
                        'message_data': {
                            'id': mensaje.id,
                            'contenido': mensaje.contenido,
                            'remitente_email': user.email,
                            'es_mio': False,
                            'fecha': timezone.localtime(mensaje.fechaHora).strftime("%Y-%m-%d %H:%M:%S"),
                            'leido': False,
                        }
                    }
                )
        except Exception:
            pass

        return Response({
            "id": mensaje.id,
            "contenido": mensaje.contenido,
            "remitente_email": user.email,
            "es_mio": True,
            "fecha": timezone.localtime(mensaje.fechaHora).strftime("%Y-%m-%d %H:%M:%S"),
            "leido": False,
        }, status=status.HTTP_201_CREATED)

    except Chat.DoesNotExist:
        return Response({"error": "Chat no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": "Error interno al enviar el mensaje."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vaciar_chat(request, chat_id):
    user = request.user
    try:
        chat = Chat.objects.select_related(
            'match', 'match__usuarioA', 'match__usuarioB'
        ).get(id=chat_id, activo=True)

        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response({"error": "No tienes permiso para esta acción."}, status=status.HTTP_403_FORBIDDEN)

        deleted_count, _ = Mensaje.objects.filter(chat_id=chat.id).delete()
        return Response({"eliminados": deleted_count}, status=status.HTTP_200_OK)

    except Chat.DoesNotExist:
        return Response({"error": "Chat no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"ERROR al vaciar chat {chat_id}: {e}")
        return Response({"error": "Error interno al vaciar el chat."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# ENDPOINTS PARA GESTIONAR EL ESTADO "CHAT ABIERTO"
# Esto evita que se envíen notificaciones cuando el usuario
# está activamente viendo el chat.
# ============================================================
from django.core.cache import cache

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def abrir_chat(request, chat_id):
    """
    Marca que el usuario tiene el chat abierto.
    Mientras esté abierto, no recibirá notificaciones de ese chat.
    """
    user = request.user
    try:
        # Validar que el chat existe y el usuario pertenece a él
        chat = Chat.objects.select_related(
            'match', 'match__usuarioA', 'match__usuarioB'
        ).get(id=chat_id, activo=True)

        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response(
                {"error": "No tienes permiso para este chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Guardar en cache que el usuario tiene este chat abierto
        # Expira en 30 minutos por si el usuario no cierra correctamente
        cache_key = f"chat_abierto_usuario_{user.id}"
        cache.set(cache_key, chat.id, timeout=1800)  # 30 minutos
        
        print(f"✅ Usuario {user.id} abrió chat {chat.id}")
        
        return Response(
            {"message": "Chat marcado como abierto", "chat_id": chat.id},
            status=status.HTTP_200_OK
        )

    except Chat.DoesNotExist:
        return Response(
            {"error": "Chat no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"ERROR al marcar chat {chat_id} como abierto: {e}")
        return Response(
            {"error": "Error interno."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cerrar_chat(request, chat_id):
    """
    Marca que el usuario cerró el chat.
    Volverá a recibir notificaciones de ese chat.
    """
    user = request.user
    try:
        # No es necesario validar permisos aquí, simplemente limpiamos el cache
        cache_key = f"chat_abierto_usuario_{user.id}"
        current_chat_id = cache.get(cache_key)
        
        # Solo limpiar si el chat que se cierra es el mismo que está abierto
        if current_chat_id == int(chat_id):
            cache.delete(cache_key)
            print(f"✅ Usuario {user.id} cerró chat {chat_id}")
        
        return Response(
            {"message": "Chat marcado como cerrado"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"ERROR al marcar chat {chat_id} como cerrado: {e}")
        return Response(
            {"error": "Error interno."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

