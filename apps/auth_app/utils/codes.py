"""Gestión de códigos de verificación de email mediante Redis.

Cada código se almacena con clave "verify:{email}", TTL de 10 minutos,
y un contador de intentos. Tras 5 intentos fallidos se invalida.
"""

import random
import logging
from datetime import datetime

from apps.auth_app.utils.redis_client import (
    set_json,
    get_json,
    delete_key,
)

logger = logging.getLogger(__name__)

DEFAULT_CODE_TTL = 600
MAX_ATTEMPTS = 5


def generate_verification_code(email: str, ttl: int = DEFAULT_CODE_TTL) -> str:
    """Genera un código de 6 dígitos para verificación de email.

    Sobrescribe cualquier código previo, resetea el contador de intentos
    y establece la fecha de creación. Almacena en Redis con TTL configurable.

    Args:
        email: Dirección de correo del usuario.
        ttl: Tiempo de vida en segundos (default: 600).

    Returns:
        Código de verificación generado.

    Raises:
        RuntimeError: Si no se puede escribir en Redis.
    """
    logger.info(f"Generando código de verificación para email: {email}")
    code = f"{random.randint(100000, 999999)}"
    key = f"verify:{email}"

    payload = {
        "code": code,
        "attempts": 0,
        "created_at": datetime.utcnow().isoformat(),
    }

    if set_json(key, payload, ttl=ttl):
        return code
    else:
        raise RuntimeError("No se pudo guardar el código en Redis.")


def verify_code(email: str, user_code: str) -> bool:
    """Verifica un código de 6 dígitos para un email.

    Valida el código contra Redis, controla el límite de 5 intentos
    y elimina la clave tras una verificación exitosa (consumo único).

    Args:
        email: Dirección de correo del usuario.
        user_code: Código ingresado por el usuario.

    Returns:
        True si el código es correcto, False en caso contrario.
    """
    key = f"verify:{email}"
    data = get_json(key)
    if not data:
        return False

    stored_code = data.get("code")
    attempts = data.get("attempts", 0)

    if attempts >= MAX_ATTEMPTS:
        delete_key(key)
        return False

    if user_code != stored_code:
        new_attempts = attempts + 1
        set_json(key, {
            "code": stored_code,
            "attempts": new_attempts,
            "created_at": data.get("created_at"),
        }, ttl=DEFAULT_CODE_TTL)
        return False

    delete_key(key)
    return True


def invalidate_code(email: str) -> None:
    """Elimina el código de verificación de Redis para un email."""
    delete_key(f"verify:{email}")


def code_exists(email: str) -> bool:
    """Verifica si existe un código de verificación activo para un email."""
    from apps.auth_app.utils.redis_client import key_exists
    return key_exists(f"verify:{email}")

