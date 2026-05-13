"""Serializers para preferencias y filtros de usuario."""

from rest_framework import serializers
from .models import Preference, Filter


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = '__all__'


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filter
        fields = ['id', 'usuario', 'filter_types', 'filter_values']
        read_only_fields = ['id']