# apps/auth_app/utils/redis_client.py
"""
Cliente Redis centralizado para toda la aplicación auth_app.
Provee operaciones básicas (get, set, setex, delete, incr, json) con manejo
de reconexión y errores controlados.

Permite:
 - Reutilizar una única conexión Redis (singleton pattern)
 - Trabajar con datos JSON automáticamente
 - Definir TTLs y prefijos de claves
 - Serializar objetos datetime/date automáticamente a ISO 8601
"""

import json
import redis
import logging
from datetime import date, datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Wrapper de redis.StrictRedis que provee métodos de conveniencia
    y manejo de errores controlado.
    """

    _instance = None  # singleton

def __new__(cls):
    if cls._instance is None:
        try:
            redis_url = getattr(settings, "REDIS_URL", None)

            # Si no existe, Redis será opcional
            if not redis_url:
                logger.warning("REDIS_URL no está configurada. Redis no será usado.")
                cls._instance = None
                return cls._instance

            cls._instance = redis.StrictRedis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30,
            )
            logger.info("Conexión Redis inicializada correctamente.")

        except Exception as e:
            logger.error(f"Error al conectar con Redis: {e}")
            cls._instance = None  # Redis opcional
    return cls._instance



# Instancia global compartida
redis_client = RedisClient()


# ----------------------------
# Funciones auxiliares JSON
# ----------------------------

def _default_json_serializer(obj):
    """
    Convierte objetos no serializables (como datetime/date) a ISO 8601.
    Lanza TypeError si no puede serializar el tipo.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Tipo no serializable: {type(obj).__name__}")


def set_json(key: str, value: dict, ttl: int = None) -> bool:
    """
    Guarda un diccionario como JSON en Redis.
    Convierte automáticamente objetos datetime/date a string.
    Args:
        key (str): nombre de la clave.
        value (dict): datos a guardar.
        ttl (int): tiempo de vida en segundos (opcional).
    Returns:
        bool: True si la operación fue exitosa.
    """
    try:
        json_value = json.dumps(value, default=_default_json_serializer)
        if ttl:
            redis_client.setex(key, ttl, json_value)
        else:
            redis_client.set(key, json_value)
        return True
    except Exception as e:
        logger.error(f"Error al guardar JSON en Redis [{key}]: {e}")
        return False


def get_json(key: str) -> dict | None:
    """
    Recupera un diccionario guardado como JSON en Redis.
    Args:
        key (str): nombre de la clave.
    Returns:
        dict | None: valor recuperado o None si no existe o hay error.
    """
    try:
        raw_value = redis_client.get(key)
        if not raw_value:
            return None
        return json.loads(raw_value)
    except Exception as e:
        logger.error(f"Error al leer JSON desde Redis [{key}]: {e}")
        return None


# ----------------------------
# Funciones básicas
# ----------------------------

def set_value(key: str, value: str, ttl: int = None) -> bool:
    """Guarda un valor string con TTL opcional."""
    try:
        if ttl:
            redis_client.setex(key, ttl, value)
        else:
            redis_client.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Error al guardar valor en Redis [{key}]: {e}")
        return False


def get_value(key: str) -> str | None:
    """Obtiene un valor string de Redis."""
    try:
        return redis_client.get(key)
    except Exception as e:
        logger.error(f"Error al obtener valor de Redis [{key}]: {e}")
        return None


def delete_key(key: str) -> bool:
    """Elimina una clave de Redis."""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error al eliminar clave Redis [{key}]: {e}")
        return False


def increment(key: str) -> int:
    """Incrementa un contador en Redis."""
    try:
        return redis_client.incr(key)
    except Exception as e:
        logger.error(f"Error al incrementar contador [{key}]: {e}")

