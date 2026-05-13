"""Modelo de imágenes de perfil de usuario.

Las imágenes se almacenan en MinIO/S3 con organización por usuario.
Se usa un nombre temporal con UUID que luego se renombra al ID real.
"""

from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from apps.auth_app.models import Usuario
import os
import uuid


def user_directory_path(instance, filename):
    """Genera ruta: imagenes/usuarios/{usuario_id}/temp_{uuid}.{ext}"""
    ext = filename.split('.')[-1].lower()
    return f"imagenes/usuarios/{instance.usuario.usuario_id}/temp_{uuid.uuid4().hex[:8]}.{ext}"


class Imagen(models.Model):
    """Imagen de perfil asociada a un usuario.

    Solo una imagen puede ser principal por usuario.
    Se almacena en MinIO/S3 con nombre definitivo tras el guardado.
    """

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to=user_directory_path)
    es_principal = models.BooleanField(default=False)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_subida']

    def __str__(self):
        return f"Imagen de {self.usuario.email} del {self.fecha_subida.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if self.es_principal:
            Imagen.objects.filter(usuario=self.usuario).exclude(pk=self.pk).update(es_principal=False)
        if is_new and self.imagen:
            self.rename_with_id()

    def rename_with_id(self):
        """Renombra el archivo temporal a: {usuario_id}_imagen_{imagen_id}.{ext}"""
        try:
            storage = default_storage
            current_name = self.imagen.name
            if not current_name:
                return
            ext = current_name.split('.')[-1].lower()
            new_name = f"imagenes/usuarios/{self.usuario.usuario_id}/{self.usuario.usuario_id}_imagen_{self.id}.{ext}"
            with self.imagen.open('rb') as f:
                saved_name = storage.save(new_name, ContentFile(f.read()))
            if storage.exists(current_name) and current_name != saved_name:
                try:
                    storage.delete(current_name)
                except Exception:
                    pass
            Imagen.objects.filter(pk=self.pk).update(imagen=saved_name)
            self.imagen.name = saved_name
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        if self.imagen and self.imagen.name:
            try:
                default_storage.delete(self.imagen.name)
            except Exception:
                pass
        super().delete(*args, **kwargs)