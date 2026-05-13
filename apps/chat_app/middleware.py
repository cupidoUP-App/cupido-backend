"""Middleware de autenticación JWT para WebSockets (Django Channels).

Lee el token JWT de la query string (?token=...) y autentica
al usuario para las conexiones WebSocket de chat y notificaciones.
"""

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from urllib.parse import parse_qs

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key):
    """Valida un JWT access token y retorna el usuario asociado.

    Busca el claim 'usuario_id' o 'user_id' en el token.
    Retorna AnonymousUser si el token es inválido o expiró.
    """
    try:
        token = AccessToken(token_key)
        user_id = token.get('usuario_id') or token.get('user_id')
        if not user_id:
            return AnonymousUser()
        return User.objects.get(usuario_id=user_id)
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JwtAuthMiddleware:
    """Middleware de autenticación JWT para conexiones WebSocket de Channels.

    Extrae el token de la query string de la URL del WebSocket
    y lo coloca en scope['user'].
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        if token_key:
            scope['user'] = await get_user_from_token(token_key)
        else:
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)