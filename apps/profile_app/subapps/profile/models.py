"""Modelo de perfil de usuario.

Contiene datos extendidos del usuario: programa académico,
ubicación, preferencias, hobbies, estatura y estado.
"""

from django.db import models
from apps.auth_app.models import Usuario, Programa, Ubicacion
from apps.preferences_app.models import Preference


class Perfil(models.Model):
    """Perfil extendido del usuario con datos personales y de matching."""

    perfil_id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, models.DO_NOTHING, blank=True, null=True)
    programa_academico = models.ForeignKey(Programa, models.DO_NOTHING, blank=True, null=True)
    ubicacion = models.ForeignKey(Ubicacion, models.DO_NOTHING, blank=True, null=True)
    preferencias = models.ForeignKey(Preference, models.DO_NOTHING, blank=True, null=True)
    hobbies = models.CharField(max_length=255, blank=True, null=True)
    estatura = models.FloatField(blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    likes = models.IntegerField(blank=True, null=True)
    fecharegistro = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'perfil'
        managed = True

    def __str__(self):
        return f"Perfil de {self.usuario}" if self.usuario else "Perfil sin usuario"
