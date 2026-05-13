"""URLs del módulo de likes. Endpoint único para interacciones LIKE/DISLIKE."""

from django.urls import path
from .views import UserInteractionView

app_name = "like_app"

urlpatterns = [
    path('interaction/', UserInteractionView.as_view(), name='user_interaction'),
]