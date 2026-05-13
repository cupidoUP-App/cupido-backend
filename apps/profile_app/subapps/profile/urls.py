"""URLs de la subapp de perfiles (profileManagement)."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileUpdateView, PerfilDetailView, PerfilAdminUpdateView,
    ProgramaViewSet, UbicacionViewSet
)

router = DefaultRouter()
router.register(r'degrees', ProgramaViewSet, basename='programa')
router.register(r'locations', UbicacionViewSet, basename='ubicacion')

urlpatterns = [
    path("update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("<int:pk>/", PerfilDetailView.as_view(), name="profile-detail"),
    path("admin/<int:pk>/", PerfilAdminUpdateView.as_view(), name="profile-admin-update"),
    path("", include(router.urls)),
]
