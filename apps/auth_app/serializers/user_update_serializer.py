"""Serializer para actualización de perfil de usuario autenticado.

Actualiza parcialmente (PATCH) nombres, apellidos, género, fecha de
nacimiento, descripción, estado de cuenta y teléfono.
"""

from datetime import date
from rest_framework import serializers
from apps.auth_app.models import Usuario, Genero
from apps.auth_app.utils.validators import calculate_age


class UserUpdateSerializer(serializers.ModelSerializer):
    """Valida y actualiza datos del perfil del usuario autenticado.

    Campos: nombres, apellidos, genero_id, fechanacimiento, descripcion,
    estadocuenta, numerotelefono. Todos opcionales (PATCH parcial).
    """

    genero_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            "nombres", "apellidos", "genero_id", "fechanacimiento",
            "descripcion", "estadocuenta", "numerotelefono",
        ]
        extra_kwargs = {
            field: {"required": False} for field in fields
        }
        extra_kwargs["descripcion"] = {"required": False, "allow_blank": True}

    def validate_nombres(self, value):
        return value.strip() if value else value

    def validate_apellidos(self, value):
        return value.strip() if value else value

    def validate_fechanacimiento(self, value: date) -> date:
        if value is None:
            return value
        if value >= date.today():
            raise serializers.ValidationError("La fecha de nacimiento debe ser en el pasado.")
        age = calculate_age(value)
        if age < 18:
            raise serializers.ValidationError("Debes tener al menos 18 años.")
        return value

    def validate_genero_id(self, value):
        if value is None:
            return value
        if not Genero.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Género inválido.")
        return value

    def update(self, instance: Usuario, validated_data: dict) -> Usuario:
        genero_id = validated_data.pop("genero_id", None)
        if genero_id is not None:
            instance.genero = Genero.objects.get(pk=genero_id)

        for field in ["nombres", "apellidos", "fechanacimiento", "descripcion", "estadocuenta", "numerotelefono"]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance


