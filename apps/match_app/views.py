"""Vistas del sistema de matching/recomendaciones.

- MatchRecommendationsView: feed de perfiles ordenados por compatibilidad
- CheckMatchView: verifica si existe match activo con otro usuario
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import date

from apps.profile_app.subapps.profile.models import Perfil
from apps.auth_app.models import Usuario
from apps.profile_app.subapps.imageUpload.models import Imagen
from apps.profile_app.subapps.imageUpload.services import generate_presigned_url

from .utils import obtener_perfil, obtener_preferencias_por_perfil, obtener_perfiles_sugeridos


class MatchRecommendationsView(APIView):
    """Genera el feed de perfiles recomendados para el usuario autenticado.

    GET /match/recommendations/
    Usa el motor de compatibilidad (match_app/utils.py) para calcular scores.
    Incluye URLs presignadas de imágenes (válidas 1 hora).
    """

    permission_classes = [IsAuthenticated]

    def calcular_edad(self, fecha_nacimiento):
        """Calcula edad en años desde una fecha de nacimiento."""
        if not fecha_nacimiento:
            return None
        today = date.today()
        edad = today.year - fecha_nacimiento.year
        if (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
            edad -= 1
        return edad

    def get_ubicacion_str(self, perfil: Perfil):
        """Convierte ubicacion_id a texto legible (Pamplona/Cúcuta)."""
        ubicacion_obj = getattr(perfil, "ubicacion", None)
        if ubicacion_obj is not None:
            nombre = getattr(ubicacion_obj, "nombre", None) or getattr(ubicacion_obj, "ciudad", None)
            if nombre:
                return nombre
        ubi_id = getattr(perfil, "ubicacion_id", None)
        if ubi_id == 1:
            return "Pamplona"
        if ubi_id == 2:
            return "Cúcuta"
        return None

    def get(self, request, *args, **kwargs):
        # 1) Usuario autenticado (JWT)
        usuario: Usuario = request.user

        # 2) Perfil asociado a ese usuario
        perfil_usuario = obtener_perfil(usuario.usuario_id)
        if not perfil_usuario:
            return Response(
                {"detail": "El usuario no tiene perfil asociado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 3) Preferencias asociadas al perfil
        preferencias = obtener_preferencias_por_perfil(perfil_usuario)
        if not preferencias:
            return Response(
                {"detail": "El usuario no tiene preferencias configuradas."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 4) Obtener perfiles sugeridos + score
        compatibles = obtener_perfiles_sugeridos(
            perfil_usuario,
            preferencias,
            limite=30,
            con_score=True,
        )

        # 5) Cargar info de Usuario para todos los perfiles de una sola vez
        usuario_ids = [perfil_usuario.usuario_id] + [
            p.usuario_id for p, _ in compatibles
        ]
        usuarios = Usuario.objects.filter(usuario_id__in=usuario_ids)
        usuarios_map = {u.usuario_id: u for u in usuarios}

        usuario_principal = usuarios_map.get(perfil_usuario.usuario_id)

        # Info del usuario principal
        user_info = {
            "usuario_id": perfil_usuario.usuario_id,
            "perfil_id": perfil_usuario.perfil_id,
            "nombre": getattr(usuario_principal, "nombres", None)
            if usuario_principal
            else None,
            "apellido": getattr(usuario_principal, "apellidos", None)
            if usuario_principal
            else None,
            # descripción viene de TABLA USUARIO
            "descripcion": getattr(usuario_principal, "descripcion", None)
            if usuario_principal
            else None,
            "hobbies": perfil_usuario.hobbies,
            "estatura": perfil_usuario.estatura,  # en metros para mostrar
            "edad": self.calcular_edad(getattr(usuario_principal, "fechanacimiento", None))
            if usuario_principal
            else None,
            "ubicacion": self.get_ubicacion_str(perfil_usuario),
        }

        # Info de las preferencias del usuario principal
        preferences_info = {
            "hobbies_preferidos": preferencias.hobbies_preferidos,
            "rango_edad_min": preferencias.rango_edad_min,
            "rango_edad_max": preferencias.rango_edad_max,
            "rango_estatura_min": preferencias.rango_estatura_min,
            "rango_estatura_max": preferencias.rango_estatura_max,
            "ubicacion": preferencias.ubicacion,
            "genero_preferido": preferencias.genero_preferido,
        }

        # 6) Obtener todas las imágenes de los perfiles recomendados
        perfil_ids = [p.usuario_id for p, _ in compatibles]
        imagenes = Imagen.objects.filter(usuario_id__in=perfil_ids).order_by('usuario_id', '-es_principal', 'fecha_subida')

        # Agrupar imágenes por usuario (usando objetos Imagen directamente)
        imagenes_map = {}
        for img in imagenes:
            usuario_id = img.usuario_id
            if usuario_id not in imagenes_map:
                imagenes_map[usuario_id] = []
            imagenes_map[usuario_id].append(img)

        # 7) Armar results: perfil recomendado + datos + score + imágenes con presigned URLs
        results = []
        for perfil, score in compatibles:
            u = usuarios_map.get(perfil.usuario_id)

            # Obtener imágenes del usuario
            user_images = imagenes_map.get(perfil.usuario_id, [])

            # Generar presigned URLs para las imágenes (válidas por 1 hora)
            # El frontend las refresca automáticamente cada 45 minutos
            main_image = None
            secondary_images = []

            if len(user_images) > 0 and user_images[0].imagen:
                # La imagen principal es la primera (ordenadas por es_principal y fecha)
                main_image = generate_presigned_url(user_images[0].imagen.name, expiration=3600)

            if len(user_images) > 1:
                # Imágenes secundarias (máximo 2)
                for img in user_images[1:3]:
                    if img.imagen:
                        url = generate_presigned_url(img.imagen.name, expiration=3600)
                        if url:
                            secondary_images.append(url)

            results.append(
                {
                    "perfil_id": perfil.perfil_id,
                    "usuario_id": perfil.usuario_id,
                    "nombre": getattr(u, "nombres", None) if u else None,
                    "apellido": getattr(u, "apellidos", None) if u else None,
                    # descripción también desde TABLA USUARIO
                    "descripcion": getattr(u, "descripcion", None) if u else None,
                    "hobbies": perfil.hobbies,
                    "estatura": perfil.estatura,  # en metros para mostrar
                    "edad": self.calcular_edad(getattr(u, "fechanacimiento", None)) if u else None,
                    "ubicacion": self.get_ubicacion_str(perfil),
                    "estado": perfil.estado,
                    "score": score,
                    "main_image": main_image,
                    "secondary_images": secondary_images,
                }
            )

        return Response(
            {
                "user": user_info,
                "preferences": preferences_info,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )


class CheckMatchView(APIView):
    """
    Verifica si existe un match activo entre el usuario autenticado y otro usuario.
    
    GET /match/check/{user_id}/
    
    Retorna:
        - has_match: boolean indicando si existe match
        - match_id: ID del match si existe (opcional)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id, *args, **kwargs):
        from .models import Match
        from django.db.models import Q
        
        current_user_id = request.user.usuario_id
        
        # Buscar match en ambas direcciones (el usuario puede ser A o B)
        match = Match.objects.filter(
            Q(usuarioA_id=current_user_id, usuarioB_id=user_id) |
            Q(usuarioA_id=user_id, usuarioB_id=current_user_id),
            estadoMatch='ACTIVO'
        ).first()
        
        if match:
            return Response({
                "has_match": True,
                "match_id": match.id
            }, status=status.HTTP_200_OK)
        
        return Response({
            "has_match": False
        }, status=status.HTTP_200_OK)

