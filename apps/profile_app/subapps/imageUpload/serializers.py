"""Serializer de imágenes con validación, compresión automática y moderación de contenido.

Valida tipo MIME (jpeg/png/webp), comprime a <400KB si es necesario,
y modera contenido inapropiado vía Sightengine API (fail-open en errores).
"""

from rest_framework import serializers
from .models import Imagen
from .services import ImageProcessor, ContentModerator


class ImagenSerializer(serializers.ModelSerializer):
    """Serializer de imágenes con validación y procesamiento automático.

    En la validación:
    1. Verifica tipo MIME permitido (jpeg, png, webp)
    2. Comprime la imagen si supera 400KB (ImageProcessor)
    3. Modera contenido con Sightengine (ContentModerator)
    """

    class Meta:
        model = Imagen
        fields = '__all__'
        read_only_fields = ('usuario',)

    def validate_imagen(self, imagen):
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        content_type = getattr(imagen, 'content_type', None)
        if content_type and content_type not in allowed_types:
            raise serializers.ValidationError("El archivo debe ser una imagen (jpeg, png, webp).")

        imagen = ImageProcessor.process_image(imagen)

        is_acceptable, message = ContentModerator.moderate_image(imagen)
        if not is_acceptable:
            raise serializers.ValidationError(message)

        return imagen
