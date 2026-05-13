"""URLs de la subapp de imágenes (photos)."""

from django.urls import path
from . import views

urlpatterns = [
    path("photos/", views.ImagenListCreateView.as_view(), name="photo-list-create"),
    path("photos/<int:pk>/", views.ImagenDetailView.as_view(), name="photo-detail"),
    path("photos/status/", views.ImagenStatusView.as_view(), name="photo-status"),
]