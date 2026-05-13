"""Serializers del módulo de perfiles.

- PerfilSerializer: serializer principal del perfil de usuario
- ProgramaSerializer: catálogo de programas académicos
- UbicacionSerializer: catálogo de ubicaciones
"""

from rest_framework import serializers
from apps.profile_app.subapps.profile.models import Perfil
from apps.auth_app.models import Programa, Ubicacion


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = "__all__"
        read_only_fields = ['perfil_id', 'usuario', 'fecharegistro']


class ProgramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programa
        fields = '__all__'


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = '__all__'