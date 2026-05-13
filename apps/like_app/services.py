"""Lógica de negocio del sistema de likes/dislikes con detección de match mutuo.

El flujo es:
1. Se crea un registro en DetallesLike por cada interacción (LIKE/DISLIKE)
2. Si ambos usuarios se dan LIKE (A→B y B→A), se detecta reciprocidad
3. Se actualiza esMutuo=True en ambos registros y se crea un Match
4. Los IDs se ordenan (menor→mayor) para consistencia del unique_together
"""

from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from apps.like_app.models import DetallesLike
from apps.match_app.models import Match
from rest_framework.exceptions import ValidationError

User = get_user_model()


def process_user_interaction(emisor_id, receptor_id, accion):
    """Procesa una interacción LIKE/DISLIKE entre dos usuarios.

    Usa transacciones atómicas para garantizar consistencia entre
    la creación del DetallesLike y el Match. Si hay match mutuo,
    también crea el registro en Match automáticamente.

    Args:
        emisor_id: ID del usuario que realiza la acción.
        receptor_id: ID del usuario receptor.
        accion: 'LIKE' o 'DISLIKE'.

    Returns:
        dict con match_found, message, status_code y opcional usuario_match.

    Raises:
        ValidationError: Si auto-interacción, receptor no existe, o match duplicado.
    """
    emisor_id = int(emisor_id)
    receptor_id = int(receptor_id)

    if emisor_id == receptor_id:
        raise ValidationError({"message": "No puedes interactuar contigo mismo."})

    try:
        User.objects.get(usuario_id=receptor_id)
    except User.DoesNotExist:
        raise ValidationError({"message": "Perfil receptor no encontrado."})

    interaccion_existente = DetallesLike.objects.filter(
        usuarioEmisor_id=emisor_id, usuarioReceptor_id=receptor_id
    ).first()

    if interaccion_existente:
        if interaccion_existente.esMutuo:
            raise ValidationError({"message": "Ya tienes un match con este usuario."})
        if interaccion_existente.estado == accion:
            raise ValidationError({"message": "Ya has interactuado con este perfil."})

    try:
        with transaction.atomic():
            es_match = False

            if accion == 'LIKE':
                like_reciproco = DetallesLike.objects.filter(
                    usuarioEmisor_id=receptor_id,
                    usuarioReceptor_id=emisor_id,
                    estado='LIKE',
                    esMutuo=False
                ).first()

                if like_reciproco:
                    es_match = True
                    like_reciproco.esMutuo = True
                    like_reciproco.save()

                    usuario_a = min(emisor_id, receptor_id)
                    usuario_b = max(emisor_id, receptor_id)

                    if not Match.objects.filter(usuarioA_id=usuario_a, usuarioB_id=usuario_b).exists():
                        Match.objects.create(usuarioA_id=usuario_a, usuarioB_id=usuario_b, estadoMatch='ACTIVO')

            if interaccion_existente:
                interaccion_existente.estado = accion
                interaccion_existente.esMutuo = es_match
                interaccion_existente.save()
            else:
                DetallesLike.objects.create(
                    usuarioEmisor_id=emisor_id, usuarioReceptor_id=receptor_id,
                    estado=accion, esMutuo=es_match
                )

            if es_match:
                return {"match_found": True, "message": "¡Match Mutuo!", "usuario_match": receptor_id, "status_code": 201}
            elif accion == 'LIKE':
                return {"match_found": False, "message": "Like registrado.", "status_code": 201}
            else:
                return {"match_found": False, "message": "Descarte registrado.", "status_code": 201}

    except IntegrityError as e:
        raise ValidationError({"message": f"Error de base de datos: {str(e)}"})