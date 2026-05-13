"""Utilidad para verificar si el perfil del usuario está completo.

Evita valores dummy creados durante el registro inicial
hasta que el usuario complete su perfil.
"""

from datetime import date
from apps.auth_app.models import Usuario


def is_profile_complete(user: Usuario) -> bool:
    """Verifica si el usuario ha completado los campos mínimos del perfil.

    Evalúa que nombres, apellidos, género y fecha de nacimiento
    no sean valores dummy ni estén vacíos.

    Args:
        user: Instancia del modelo Usuario.

    Returns:
        True si el perfil está completo, False en caso contrario.
    """
    if not isinstance(user, Usuario):
        return False
    if not user.nombres or user.nombres.strip().lower() == "dummy":
        return False
    if not user.apellidos or user.apellidos.strip().lower() == "dummy":
        return False
    if not user.genero:
        return False
    if not user.fechanacimiento or user.fechanacimiento >= date.today():
        return False
    return True





    


