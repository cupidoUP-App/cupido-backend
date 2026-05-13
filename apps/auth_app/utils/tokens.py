"""Utilidades para generación y gestión de tokens JWT.

Usa djangorestframework-simplejwt para crear tokens access/refresh
y agregar tokens a la blacklist cuando corresponda.
"""

from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)


def create_jwt_for_user(user) -> dict:
    """Genera tokens JWT (access + refresh) para un usuario.

    Args:
        user: Instancia del modelo Usuario autenticado.

    Returns:
        dict con "access" y "refresh".

    Raises:
        Exception: Si no se pueden generar los tokens.
    """
    try:
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    except Exception as e:
        logger.error(f"Error al generar tokens JWT: {e}")
        raise


def blacklist_token(refresh_token: str) -> bool:
    """Invalida un refresh token agregándolo a la blacklist.

    Args:
        refresh_token: Token refresh a invalidar.

    Returns:
        True si se invalidó correctamente, False en caso contrario.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return True
    except Exception as e:
        logger.warning(f"No se pudo invalidar el token: {e}")
        return False
