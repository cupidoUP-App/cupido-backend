"""Configuración principal de Django para el proyecto Cupido.

Secciones clave:
- JWT: tokens access (30 min) y refresh (7 días) con rotación y blacklist
- Channels: Redis como channel layer para WebSockets
- MinIO/S3: almacenamiento de imágenes con django-storages
- DRF: paginación, autenticación JWT por defecto
- Rate limiting: protección en registro, verificación y login
- CORS: orígenes permitidos desde variables de entorno
- Sightengine: credenciales para moderación de contenido
"""

from pathlib import Path
from datetime import timedelta
import os
from urllib.parse import urlparse
import dj_database_url
from dotenv import load_dotenv

# -------------------------
# Load environment variables
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# -------------------------
# Basic paths and keys
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "backend.cupidocol.com"  # valor por defecto para producción
).split(",")

# Validación de variables críticas (simplificada con if anidado)
if not SECRET_KEY:
    if not os.getenv("DATABASE_URL"):
        if not RECAPTCHA_SECRET_KEY:
            raise RuntimeError("Variables críticas no encontradas: SECRET_KEY, DATABASE_URL, RECAPTCHA_SECRET_KEY")
        raise RuntimeError("Variables críticas no encontradas: SECRET_KEY y DATABASE_URL")
    if not RECAPTCHA_SECRET_KEY:
        raise RuntimeError("Variables críticas no encontradas: SECRET_KEY y RECAPTCHA_SECRET_KEY")
    raise RuntimeError("Variable crítica no encontrada: SECRET_KEY")
if not os.getenv("DATABASE_URL"):
    if not RECAPTCHA_SECRET_KEY:
        raise RuntimeError("Variables críticas no encontradas: DATABASE_URL y RECAPTCHA_SECRET_KEY")
    raise RuntimeError("Variable crítica no encontrada: DATABASE_URL")
if not RECAPTCHA_SECRET_KEY:
    raise RuntimeError("Variable crítica no encontrada: RECAPTCHA_SECRET_KEY")

# -------------------------
# Locale / Time
# -------------------------
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# -------------------------
# CORS Configuration
# -------------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://cupidocol.com").split(",")
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "https://cupidocol.com").split(",")
CORS_ALLOW_CREDENTIALS = True


def _extract_host(value: str) -> str | None:
    trimmed = (value or "").strip()
    if not trimmed:
        return None
    parsed = urlparse(trimmed if "://" in trimmed else f"https://{trimmed}")
    return parsed.hostname


_extra_hosts = [
    host
    for source in (FRONTEND_URL + CORS_ALLOWED_ORIGINS)
    if (host := _extract_host(source))
]

ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS + _extra_hosts))

# -------------------------
# Applications
# -------------------------
INSTALLED_APPS = [
    # web Socket for Chat Services
    "channels",
    "daphne",
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Local apps
    "apps.auth_app",
    "apps.match_app",
    "apps.profile_app",
    "apps.reports_app",
    "apps.chat_app",
    "apps.preferences_app",
    "apps.notificacion_app",
    'apps.like_app',
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "storages",  # Feature: imageUpload - django-storages para MinIO/S3
]

# -------------------------
# Custom User Model
# -------------------------
AUTH_USER_MODEL = "auth_app.Usuario"

# -------------------------
# Middleware
# -------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

#Aplication ASGI que usara CHANNELS
ASGI_APPLICATION = 'config.asgi.application'

# -------------------------
# Database
# -------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=False,
    )
}

# -------------------------
# Redis / Cache
# -------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://default:enncefrd2yomncab@190.90.114.214:6379")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
    }
}

# -------------------------
# Email Configuration
# -------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "cupidoup1@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "nzboyoqvawpbhcew")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "cupidoup1@gmail.com")

# -------------------------
# Static files
# -------------------------
STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------
# Feature: imageUpload - MinIO / S3 Object Storage Configuration
# -------------------------
# Lógica de negocio: Usamos MinIO como storage de objetos S3-compatible para
# almacenar imágenes de perfil de forma escalable y portable (dev/prod).
# En producción: MINIO_ENDPOINT=http://190.90.114.214:9000

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "multimediacupido")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "False").lower() in ("true", "1", "yes")
MINIO_REGION = os.getenv("MINIO_REGION", "")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", MINIO_ENDPOINT)

# Configurar django-storages solo si MinIO está configurado
if MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": MINIO_ACCESS_KEY,
                "secret_key": MINIO_SECRET_KEY,
                "bucket_name": MINIO_BUCKET_NAME,
                "endpoint_url": MINIO_ENDPOINT,
                "region_name": MINIO_REGION if MINIO_REGION else None,
                "use_ssl": MINIO_USE_SSL,
                "file_overwrite": False,
                "default_acl": None,
                "querystring_auth": False,
                "addressing_style": "path",
                "signature_version": "s3v4",
            },
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    # Actualizar MEDIA_URL para apuntar a MinIO
    MEDIA_URL = f"{MINIO_PUBLIC_URL}/{MINIO_BUCKET_NAME}/"

# Configuración de límites de fotos
PHOTO_MAX_UPLOAD_SIZE = int(os.getenv('PHOTO_MAX_UPLOAD_SIZE', 400 * 1024))  # 400KB
PHOTO_MAX_FILES = int(os.getenv('PHOTO_MAX_FILES', 3))

# -------------------------
# Feature: imageUpload - Sightengine (Moderación de Contenido)
# -------------------------
# Detecta contenido inapropiado: desnudez, violencia, armas, drogas
# Si el servicio falla, la imagen se acepta (fail-open)
SIGHTENGINE_API_USER = os.getenv('SIGHTENGINE_API_USER', '')
SIGHTENGINE_API_SECRET = os.getenv('SIGHTENGINE_API_SECRET', '')

# -------------------------
# REST Framework
# -------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# -------------------------
# JWT Configuration
# -------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # Aumentado de 15 a 30 minutos para mejor UX
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "usuario_id",
    "USER_ID_CLAIM": "usuario_id",  # CRÍTICO: debe coincidir con USER_ID_FIELD
    "UPDATE_LAST_LOGIN": False,  # No actualizar last_login en cada refresh (mejor performance)
}

# -------------------------
# Password Validators
# -------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------
# Proxy / HTTPS
# -------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -------------------------
# Production Security
# -------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_SSL_REDIRECT = not DEBUG

# -------------------------
# Logging
# -------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],  
            "capacity": 1500,
            "expiry": 10,
            "group_expiry": 86400,
            "channel_capacity": {
                "http.request": 200,
                "http.response*": 100,
                "websocket.send*": 500,
                "websocket.receive*": 500,
            },
        },
    },
}
