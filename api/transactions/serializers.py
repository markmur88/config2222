from rest_framework import serializers
from api.transactions.models import Transaction, SEPA

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__' 

class SEPASerializer(serializers.ModelSerializer):
    class Meta:
        model = SEPA
        fields = '__all__' 