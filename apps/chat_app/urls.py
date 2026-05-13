"""URLs REST del módulo de chat.

Endpoints:
- GET / -> lista de chats del usuario
- GET /<chat_id>/mensajes/ -> historial de mensajes
- POST /<chat_id>/enviar/ -> enviar mensaje (fallback REST)
- POST /<chat_id>/vaciar/ -> eliminar todos los mensajes
- POST /<chat_id>/abrir/ -> marcar chat como abierto (suspende notificaciones)
- POST /<chat_id>/cerrar/ -> marcar chat como cerrado
"""

from django.urls import path
from . import views

urlpatterns = [
    path('<int:chat_id>/mensajes/', views.obtener_mensajes_chat, name='obtener-mensajes'),
    path('<int:chat_id>/enviar/', views.enviar_mensaje, name='enviar-mensaje'),
    path('<int:chat_id>/vaciar/', views.vaciar_chat, name='vaciar-chat'),
    path('<int:chat_id>/abrir/', views.abrir_chat, name='abrir-chat'),
    path('<int:chat_id>/cerrar/', views.cerrar_chat, name='cerrar-chat'),
    path('', views.obtener_lista_chats, name='obtener_lista_chats'),
]
