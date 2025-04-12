from rest_framework import serializers
from api.collection.models import Mandate, Collection

class MandateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mandate
        fields = '__all__'

class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'