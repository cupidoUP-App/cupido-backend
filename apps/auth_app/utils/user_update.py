"""Utilidad para generar respuesta estructurada tras actualizar perfil."""

from apps.auth_app.models import Usuario


def get_user_update_response_data(user: Usuario) -> dict:
    """Genera la respuesta estándar para PATCH /user-update/.

    Args:
        user: Instancia del usuario actualizada.

    Returns:
        dict con mensaje, estado y datos básicos del usuario.
    """
    return {
        "message": "Perfil actualizado correctamente.",
        "estado": user.estadocuenta,
        "user": {
            "usuario_id": user.usuario_id,
            "nombres": user.nombres,
            "apellidos": user.apellidos,
            "email": user.email,
            "genero": user.genero.genero_id if user.genero else None,
            "genero_descripcion": user.genero.descripcion if user.genero else None,
            "fechanacimiento": user.fechanacimiento,
            "descripcion": user.descripcion,
            "estadocuenta": user.estadocuenta,
            "numerotelefono": user.numerotelefono,
        },
    }

