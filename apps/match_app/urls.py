"""URLs del módulo de matching.

Endpoints:
- recommendations/ - feed de perfiles recomendados
- refresh-images/ - refresca URLs presignadas
- refresh-profile-images/ - refresca URLs de imágenes de perfil
- check/<user_id>/ - verifica match activo con otro usuario
"""

from django.urls import path
from .views import MatchRecommendationsView, CheckMatchView
from .views_refresh import RefreshImageURLsView, RefreshMatchImagesView

urlpatterns = [
    path("recommendations/", MatchRecommendationsView.as_view(), name="match-recommendations"),
    path("refresh-images/", RefreshImageURLsView.as_view(), name="refresh-image-urls"),
    path("refresh-profile-images/", RefreshMatchImagesView.as_view(), name="refresh-profile-images"),
    path("check/<int:user_id>/", CheckMatchView.as_view(), name="check-match"),
]

