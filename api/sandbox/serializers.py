from rest_framework import serializers
from api.sandbox.models import IncomingCollection

class IncomingCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomingCollection
        fields = "__all__"

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser positivo.")
        return value
 