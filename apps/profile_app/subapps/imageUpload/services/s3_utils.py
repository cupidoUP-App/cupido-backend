"""
Utilidades para generar presigned URLs de MinIO/S3.

Como las imágenes ahora son privadas, necesitamos generar URLs firmadas
temporalmente para que el frontend pueda acceder a ellas.
"""
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


def get_s3_client():
    """Crea y retorna un cliente S3 configurado para MinIO con firma v4."""
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name=settings.MINIO_REGION if settings.MINIO_REGION else None,
        config=boto3.session.Config(signature_version='s3v4')
    )


def generate_presigned_url(image_key: str, expiration: int = 3600) -> str | None:
    """Genera una presigned URL temporal para acceder a una imagen privada en MinIO.

    Args:
        image_key: Ruta del archivo en MinIO (ej: 'imagenes/usuarios/49/49_imagen_69.jpg').
        expiration: Segundos de validez de la URL (default: 3600 = 1 hora).

    Returns:
        URL firmada o None si falla.
    """
    if not image_key:
        return None
    try:
        return get_s3_client().generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.MINIO_BUCKET_NAME, 'Key': image_key},
            ExpiresIn=expiration
        )
    except ClientError as e:
        logger.error(f"Error generando presigned URL para {image_key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado generando presigned URL: {e}")
        return None


def generate_presigned_urls_batch(image_keys: list[str], expiration: int = 3600) -> dict[str, str]:
    """Genera presigned URLs para múltiples imágenes en lote.

    Args:
        image_keys: Lista de rutas de archivos en MinIO.
        expiration: Segundos de validez (default: 3600).

    Returns:
        dict: {image_key: presigned_url} con None para las que fallaron.
    """
    if not image_keys:
        return {}
    s3_client = get_s3_client()
    urls = {}
    for key in image_keys:
        if not key:
            continue
        try:
            urls[key] = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.MINIO_BUCKET_NAME, 'Key': key},
                ExpiresIn=expiration
            )
        except Exception as e:
            logger.error(f"Error generando URL para {key}: {e}")
            urls[key] = None
    return urls
