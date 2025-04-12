from rest_framework import serializers
from api.accounts.models import Account

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'  # Incluye todos los campos del modelo 