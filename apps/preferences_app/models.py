"""Modelos de preferencias y filtros de usuario para el sistema de matching."""

from django.db import models
from apps.auth_app.models import Usuario


class Preference(models.Model):
    """Preferencias de matching de un usuario (edad, estatura, ubicación, género, hobbies)."""

    id = models.AutoField(primary_key=True)
    rango_edad_min = models.PositiveIntegerField(null=True, blank=True)
    rango_edad_max = models.PositiveIntegerField(null=True, blank=True)
    rango_estatura_min = models.PositiveIntegerField(null=True, blank=True)
    rango_estatura_max = models.PositiveIntegerField(null=True, blank=True)
    ubicacion = models.CharField(max_length=100, null=True, blank=True)
    genero_preferido = models.CharField(max_length=50, null=True, blank=True)
    hobbies_preferidos = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Preferencias #{self.id}"


class Filter(models.Model):
    """Filtros adicionales del usuario (JSON) para refinar el matching."""

    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='filters', default=1)
    filter_types = models.JSONField(default=list)
    filter_values = models.JSONField(default=list)

    def __str__(self):
        return f"Filtros del usuario {self.usuario_id}"
