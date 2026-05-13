"""URLs REST del módulo de notificaciones (ViewSet router)."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacionViewSet

router = DefaultRouter()
router.register(r'', NotificacionViewSet, basename='notificacion')

urlpatterns = [
    path('', include(router.urls)),
]
