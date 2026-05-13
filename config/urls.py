"""Configuración raíz de URLs de la API de Cupido.

Incluye:
- Admin de Django
- API root con lista de endpoints
- Namespaces para cada app (auth, profile, match, reports, chat, preferences, notificaciones, like)
- Refresh de JWT
- Documentación Swagger/OpenAPI (drf-spectacular)
- Archivos media en DEBUG
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

API_TITLE = "Cupido API"
API_VERSION = "v1"


def root_view(request):
    return JsonResponse({
        "message": "Bienvenido a la API de Cupido",
        "version": API_VERSION,
        "endpoints": {
            "auth": "/api/v1/auth/",
            "profile": "/api/v1/profile/",
            "match": "/api/v1/match/",
            "reports": "/api/v1/reports/",
            "chat": "/api/v1/chat/",
            "preferences": "/api/v1/preferences/preferences/",
            "filtros": "/api/v1/preferences/filters/",
            "notificaciones": "/api/v1/notificaciones/",
        }
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root_view, name="api-root"),

    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/", include(("apps.auth_app.urls", "auth_app"), namespace="auth")),
    path("api/v1/profile/", include(("apps.profile_app.urls", "profile_app"), namespace="profile")),
    path("api/v1/match/", include(("apps.match_app.urls", "match_app"), namespace="match")),
    path("api/v1/reports/", include(("apps.reports_app.urls", "reports_app"), namespace="reports")),
    path("api/v1/chat/", include(("apps.chat_app.urls", "chat_app"), namespace="chat")),
    path("api/v1/preferences/", include(("apps.preferences_app.urls", "preferences_app"), namespace="preferences")),
    path("api/v1/notificaciones/", include(("apps.notificacion_app.urls", "notificacion_app"), namespace="notificaciones")),
    path('api/v1/like/', include('apps.like_app.urls')),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


