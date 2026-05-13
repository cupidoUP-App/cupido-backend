"""Motor de compatibilidad y generación de recomendaciones.

Provee funciones para:
- Normalizar hobbies y ubicaciones
- Filtrar perfiles por preferencias (género, edad, estatura, hobbies, ubicación)
- Calcular score de compatibilidad
- Generar feed de perfiles sugeridos excluyendo usuarios ya interactuados
"""

from typing import Optional, Set, List
import json

from apps.profile_app.subapps.profile.models import Perfil
from apps.preferences_app.models import Preference
from apps.auth_app.models import Usuario


# =========================================
# Helpers
# =========================================

def normalizar_hobbies(cadena: Optional[str]) -> Set[str]:
    """Convierte hobbies en un set de strings normalizados (minúsculas, sin espacios)."""
    if not cadena:
        return set()
    cadena = cadena.strip()
    if cadena.startswith("[") and cadena.endswith("]"):
        try:
            items = json.loads(cadena)
        except Exception:
            items = cadena.split(",")
    else:
        items = cadena.split(",")
    return {str(h).strip().lower() for h in items if str(h).strip()}


def obtener_usuario_de_perfil(perfil: Perfil) -> Optional[Usuario]:
    """Retorna el Usuario asociado a un Perfil."""
    usuario = getattr(perfil, "usuario", None)
    if usuario is not None:
        return usuario
    user_id = getattr(perfil, "usuario_id", None)
    if user_id is None:
        return None
    return Usuario.objects.filter(usuario_id=user_id).first()


def genero_coincide_con_preferencia(perfil: Perfil, preferencias: Preference) -> bool:
    """Evalúa si el género del perfil coincide con la preferencia.

    Reglas: 'mujer' -> id=2, 'hombre' -> id=1, 'otros'/'otro' -> ids 1,2,3.
    Sin preferencia definida: no filtra (True).
    """
    pref = (preferencias.genero_preferido or "").strip().lower()
    if not pref:
        return True
    usuario = obtener_usuario_de_perfil(perfil)
    if not usuario:
        return False
    genero_id = getattr(usuario, "genero_id", None)
    if genero_id is None:
        return False
    if pref == "mujer":
        return genero_id == 2
    if pref == "hombre":
        return genero_id == 1
    if pref in ("otros", "otro"):
        return genero_id in {1, 2, 3}
    return True


def normalizar_ubicacion_texto(texto: Optional[str]) -> Optional[int]:
    """Convierte texto de ubicación a ID numérico.

    'Pamplona' -> 1, 'Cúcuta' -> 2, otros -> None.
    """
    if not texto:
        return None
    t = texto.strip().lower()
    t = t.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    if "pamplona" in t:
        return 1
    if "cucuta" in t:
        return 2
    return None


def ubicacion_coincide(preferencias: Preference, perfil: Perfil) -> bool:
    """True si la ubicación del perfil coincide con la preferida."""
    pref_ubi_id = normalizar_ubicacion_texto(preferencias.ubicacion)
    if pref_ubi_id is None:
        return True
    perfil_ubi_id = getattr(perfil, "ubicacion_id", None)
    if perfil_ubi_id is None:
        return False
    return perfil_ubi_id == pref_ubi_id


def estatura_en_cm(perfil: Perfil) -> Optional[int]:
    """Convierte estatura de metros (Perfil) a centímetros (Preference)."""
    est = getattr(perfil, "estatura", None)
    if est is None:
        return None
    try:
        return int(round(float(est) * 100))
    except (TypeError, ValueError):
        return None


# ===============================
# Obtener perfil y preferencias
# ===============================

def obtener_perfil(user_id: int) -> Optional[Perfil]:
    """Obtiene el Perfil de un usuario por su ID."""
    return Perfil.objects.filter(usuario_id=user_id).first()


def obtener_preferencias_por_perfil(perfil: Perfil) -> Optional[Preference]:
    """Obtiene las preferencias asociadas a un Perfil."""
    pref_id = getattr(perfil, "preferencias_id", None)
    if not pref_id:
        return None
    return Preference.objects.filter(id=pref_id).first()


def obtener_otros_perfiles(perfil: Perfil):
    """Retorna todos los perfiles excepto el del usuario."""
    return Perfil.objects.exclude(usuario_id=perfil.usuario_id)


# ===============================
# Validación de compatibilidad
# ===============================

def perfil_cumple_preferencias(perfil: Perfil, preferencias: Preference) -> bool:
    """Evalúa si un perfil cumple TODOS los filtros duros de preferencias.

    Filtros: género (obligatorio), estatura, hobbies (al menos 1 en común),
    edad y ubicación.
    """
    if not genero_coincide_con_preferencia(perfil, preferencias):
        return False

    estatura_cm = estatura_en_cm(perfil)
    if preferencias.rango_estatura_min is not None and estatura_cm is not None:
        if estatura_cm < preferencias.rango_estatura_min:
            return False
    if preferencias.rango_estatura_max is not None and estatura_cm is not None:
        if estatura_cm > preferencias.rango_estatura_max:
            return False

    pref_hobbies = normalizar_hobbies(preferencias.hobbies_preferidos)
    perfil_hobbies = normalizar_hobbies(perfil.hobbies)
    if pref_hobbies and not (pref_hobbies & perfil_hobbies):
        return False

    edad_perfil = getattr(perfil, "edad", None)
    if preferencias.rango_edad_min is not None and edad_perfil is not None:
        if edad_perfil < preferencias.rango_edad_min:
            return False
    if preferencias.rango_edad_max is not None and edad_perfil is not None:
        if edad_perfil > preferencias.rango_edad_max:
            return False

    if not ubicacion_coincide(preferencias, perfil):
        return False

    return True


# ===============================
# Score de compatibilidad
# ===============================

def calcular_score(preferencias: Preference, perfil: Perfil) -> float:
    """Calcula un puntaje de compatibilidad entre preferencias y perfil.

    Sistema de puntuación:
    - +1 género coincide
    - +N hobbies en común
    - +1 estatura en rango
    - +1 edad en rango
    - +1 ubicación coincide
    Máximo teórico: 5 + hobbies_comunes.

    Returns:
        0.0 si el género no coincide (filtro obligatorio).
    """
    if not genero_coincide_con_preferencia(perfil, preferencias):
        return 0.0

    score = 1.0

    pref_hobbies = normalizar_hobbies(preferencias.hobbies_preferidos)
    perfil_hobbies = normalizar_hobbies(perfil.hobbies)
    score += float(len(pref_hobbies & perfil_hobbies))

    estatura_cm = estatura_en_cm(perfil)
    if (preferencias.rango_estatura_min is not None and preferencias.rango_estatura_max is not None
            and estatura_cm is not None):
        if preferencias.rango_estatura_min <= estatura_cm <= preferencias.rango_estatura_max:
            score += 1.0

    edad_perfil = getattr(perfil, "edad", None)
    if (preferencias.rango_edad_min is not None and preferencias.rango_edad_max is not None
            and edad_perfil is not None):
        if preferencias.rango_edad_min <= edad_perfil <= preferencias.rango_edad_max:
            score += 1.0

    if ubicacion_coincide(preferencias, perfil):
        score += 1.0

    return score


# ===============================
# Feed de perfiles sugeridos
# ===============================

def obtener_usuarios_ya_interactuados(user_id: int) -> Set[int]:
    """Retorna IDs de usuarios con los que ya hubo interacción previa.

    Excluye estos usuarios de las recomendaciones para evitar
    mostrar perfiles ya vistos.
    """
    from apps.like_app.models import DetallesLike
    return set(DetallesLike.objects.filter(
        usuarioEmisor_id=user_id
    ).values_list('usuarioReceptor_id', flat=True))


def obtener_perfiles_sugeridos(
    perfil_usuario: Perfil,
    preferencias: Preference,
    limite: int = 100,
    con_score: bool = False,
):
    """Genera el feed de perfiles recomendados para un usuario.

    Ordena por score descendente. Excluye usuarios ya interactuados.
    Incluye perfiles que no pasan todos los filtros duros pero tienen
    score >= 1 (género coincide).

    Args:
        perfil_usuario: Perfil del usuario solicitante.
        preferencias: Preferencias del usuario.
        limite: Máximo de resultados.
        con_score: Si True, retorna tuplas (Perfil, score).

    Returns:
        Lista de Perfiles o tuplas (Perfil, score) según con_score.
    """
    otros = obtener_otros_perfiles(perfil_usuario)
    usuarios_excluidos = obtener_usuarios_ya_interactuados(perfil_usuario.usuario_id)

    compatibles: List[tuple[Perfil, float]] = []
    for p in otros:
        if p.usuario_id in usuarios_excluidos:
            continue
        hard_ok = perfil_cumple_preferencias(p, preferencias)
        score = calcular_score(preferencias, p)
        if hard_ok or score >= 1:
            compatibles.append((p, score))

    compatibles.sort(key=lambda x: x[1], reverse=True)

    if con_score:
        return compatibles[:limite]
    return [p for p, _ in compatibles[:limite]]

