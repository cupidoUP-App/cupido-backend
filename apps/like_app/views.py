"""Vista del sistema de likes/dislikes.

Endpoint único POST /like/interaction/ que delega la lógica
de negocio en services.py (process_user_interaction).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .services import process_user_interaction


class UserInteractionView(APIView):
    """Endpoint para registrar interacciones LIKE/DISLIKE entre usuarios.

    POST: Recibe receptor_id y accion ('LIKE'/'DISLIKE') del usuario autenticado.
    La lógica de match mutuo se maneja en process_user_interaction.
    """

    def post(self, request, format=None):
        try:
            emisor_id = request.user.usuario_id
            receptor_id = request.data.get('receptor_id')
            accion = request.data.get('accion', 'LIKE').upper()

            result = process_user_interaction(emisor_id, receptor_id, accion)

            return Response(
                {
                    "match_found": result["match_found"],
                    "message": result["message"],
                    **({"usuario_match": receptor_id} if result["match_found"] else {})
                },
                status=result["status_code"]
            )

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)