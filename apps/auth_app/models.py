from django.db import models
from django.contrib.auth.models import AbstractUser


class Genero(models.Model):
    """Catálogo de géneros para usuarios (Masculino, Femenino, Otro)."""

    genero_id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=30)
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'genero'


class Ubicacion(models.Model):
    """Catálogo de ubicaciones/ciudades disponibles (Pamplona, Cúcuta)."""

    ubicacion_id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ubicacion'


class Programa(models.Model):
    """Catálogo de programas académicos universitarios."""

    programa_id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=60)
    fecha_creacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'programa'


class Usuario(AbstractUser):
    """
    Modelo principal de usuario. Hereda de AbstractUser pero adaptado
    a la base de datos legacy con campos en español.

    Usa email como USERNAME_FIELD en lugar de username.
    La contraseña se almacena en 'contrasena' (no en 'password').
    Proxies first_name/last_name/password/id a los campos legacy.
    """

    usuario_id = models.AutoField(primary_key=True)
    genero = models.ForeignKey(Genero, models.DO_NOTHING, blank=True, null=True)
    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)
    fechanacimiento = models.DateField(blank=True)
    email = models.CharField(unique=True, max_length=60)
    contrasena = models.CharField(max_length=255)
    numerotelefono = models.CharField(blank=True, max_length=15)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    fecharegistro = models.DateTimeField(blank=True, null=True)
    estadocuenta = models.CharField(max_length=1, blank=True, null=True)
    tyc = models.BooleanField(blank=True, null=True)
    firma = models.TextField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombres', 'apellidos']

    class Meta:
        db_table = 'usuario'

    @property
    def first_name(self):
        """Proxy: retorna nombres en lugar de first_name."""
        return self.nombres

    @first_name.setter
    def first_name(self, value):
        self.nombres = value

    @property
    def last_name(self):
        """Proxy: retorna apellidos en lugar de last_name."""
        return self.apellidos

    @last_name.setter
    def last_name(self, value):
        self.apellidos = value

    @property
    def password(self):
        """Proxy: retorna contrasena en lugar de password."""
        return self.contrasena

    @password.setter
    def password(self, value):
        self.contrasena = value

    @property
    def id(self):
        """Proxy: retorna usuario_id como id para compatibilidad con SimpleJWT."""
        return self.usuario_id

    def get_full_name(self):
        return f"{self.nombres} {self.apellidos}"

    def get_short_name(self):
        return self.nombres



