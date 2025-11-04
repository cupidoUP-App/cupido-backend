# apps/auth_app/serializers/user_get_serializer.py

from rest_framework import serializers
from apps.auth_app.models import Usuario


class UserGetSerializer(serializers.Serializer):
    """
    Serializa todos los campos del perfil de usuario para respuestas GET.
    Este serializer es de solo lectura y devuelve toda la información del usuario autenticado.
    """
    
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
    
    # Foreign key relations
    programa_id = serializers.IntegerField(allow_null=True, source='programa.programa_id')
    ubicacion_id = serializers.IntegerField(allow_null=True, source='ubicacion.ubicacion_id')
    genero_id = serializers.IntegerField(allow_null=True, source='genero.genero_id')


def serialize_user_profile(user: Usuario) -> dict:
    """
    Serializa todos los campos del usuario en un diccionario.
    Maneja las relaciones FK de forma segura.
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
        "programa_id": user.perfil_set.first().programa_academico.programa_id if user.perfil_set.first() and user.perfil_set.first().programa_academico else None,
        "ubicacion_id": user.ubicacion.ubicacion_id if user.ubicacion else None,
    }

