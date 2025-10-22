# apps/branches/serializers.py

from rest_framework import serializers
from .models import Sube

class SubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sube
        fields = '__all__'  # Sube modelindeki tüm alanları dahil et