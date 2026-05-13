"""Utilidad para obtener datos completos del perfil del usuario autenticado."""

from apps.auth_app.serializers.user_get_serializer import serialize_user_profile
from apps.auth_app.models import Usuario


def get_user_profile_data(user: Usuario) -> dict:
    """Obtiene todos los datos del perfil del usuario y su estado.

    Mantiene sincronizado el campo estadocuenta si difiere del estado
    calculado. Usa serialize_user_profile para los datos del usuario.

    Args:
        user: Instancia del usuario autenticado.

    Returns:
        dict con estado, should_complete_profile y user_data.
    """
    estado = user.estadocuenta

    if getattr(user, "estadocuenta", None) != estado:
        user.estadocuenta = estado
        user.save(update_fields=["estadocuenta"])

    user_data = serialize_user_profile(user)

    return {
        "estado": estado,
        "should_complete_profile": estado in ["1", "2", "3"],
        "user": user_data,
    }

