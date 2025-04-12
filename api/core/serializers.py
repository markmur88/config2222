from rest_framework import serializers
from api.core.models import CoreModel  # Asegúrate de que CoreModel esté definido en models.py

class CoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoreModel
        fields = '__all__'
