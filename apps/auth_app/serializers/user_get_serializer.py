"""Serializer de solo lectura para obtener datos completos del perfil de usuario."""

from rest_framework import serializers
from apps.auth_app.models import Usuario


class UserGetSerializer(serializers.Serializer):
    """Serializa todos los campos del perfil de usuario para respuestas GET."""

    usuario_id = serializers.IntegerField()
    nombres = serializers.CharField()
    apellidos = serializers.CharField()
    email = serializers.EmailField()
    fechanacimiento = serializers.DateField()
    numerotelefono = serializers.CharField()
    descripcion = serializers.CharField(allow_null=True, allow_blank=True)
    fecharegistro = serializers.DateTimeField(allow_null=True)
    estadocuenta = serializers.CharField(allow_null=True, allow_blank=True)
    tyc = serializers.BooleanField(allow_null=True)
    genero_id = serializers.IntegerField(allow_null=True, source='genero.genero_id')


def serialize_user_profile(user: Usuario) -> dict:
    """Convierte un usuario en un dict serializado manejando FK de forma segura.

    Args:
        user: Instancia del modelo Usuario.

    Returns:
        dict con todos los campos planos del usuario.
    """
    return {
        "usuario_id": user.usuario_id,
        "nombres": user.nombres,
        "apellidos": user.apellidos,
        "email": user.email,
        "fechanacimiento": user.fechanacimiento,
        "numerotelefono": user.numerotelefono,
        "descripcion": user.descripcion,
        "fecharegistro": user.fecharegistro,
        "estadocuenta": user.estadocuenta,
        "tyc": user.tyc,
        "genero_id": user.genero.genero_id if user.genero else None,
    }

