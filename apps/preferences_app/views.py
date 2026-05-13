"""ViewSets para preferencias y filtros de usuario."""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Preference, Filter
from .serializers import PreferenceSerializer, FilterSerializer


class PreferenceViewSet(viewsets.ModelViewSet):
    """CRUD de preferencias de matching del usuario."""

    serializer_class = PreferenceSerializer
    permission_classes = [AllowAny]
    queryset = Preference.objects.all()


class FilterViewSet(viewsets.ModelViewSet):
    """CRUD de filtros adicionales. Filtrable por ?usuario=ID."""

    queryset = Filter.objects.all()
    serializer_class = FilterSerializer

    def get_queryset(self):
        queryset = Filter.objects.all()
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id is not None:
            queryset = queryset.filter(usuario_id=usuario_id)
        return queryset