# apps/sepa_payment/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class SepaCreditTransfer(models.Model):
    payment_id = models.CharField(max_length=50, primary_key=True)
    auth_id = models.CharField(max_length=50)
    transaction_status = models.CharField(max_length=10)
    purpose_code = models.CharField(max_length=4)
    requested_execution_date = models.DateField()
    debtor_name = models.CharField(max_length=140)
    debtor_iban = models.CharField(max_length=34, validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')])
    debtor_currency = models.CharField(max_length=3)
    creditor_name = models.CharField(max_length=70)
    creditor_iban = models.CharField(max_length=34, validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')])
    creditor_currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    end_to_end_id = models.CharField(max_length=35)
    instruction_id = models.CharField(max_length=35)
    remittance_structured = models.CharField(max_length=140, null=True, blank=True)
    remittance_unstructured = models.CharField(max_length=140, null=True, blank=True)
    debtor_address_country = models.CharField(max_length=2)
    debtor_address_street = models.CharField(max_length=70)
    debtor_address_zip = models.CharField(max_length=70)
    creditor_address_country = models.CharField(max_length=2)
    creditor_address_street = models.CharField(max_length=70)
    creditor_address_zip = models.CharField(max_length=70)
    creditor_agent_id = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transferencia SEPA'
        verbose_name_plural = 'Transferencias SEPA'

    def __str__(self):
        return f'Transferencia SEPA {self.payment_id}'
    

# apps/sepa_payment/models.py
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

class SepaCreditTransferStatus(models.Model):
    """
    Almacena el historial de estados de cada transferencia SEPA.
    """
    STATUS_CHOICES = [
        ('RJCT', 'Rechazada'),
        ('RCVD', 'Recibida'),
        ('ACCP', 'Aceptada'),
        ('ACTC', 'Aceptada con cambio técnico'),
        ('ACSP', 'Aceptada con cambio semántico'),
        ('ACSC', 'Aceptada con cambio sintáctico'),
        ('ACWC', 'Aceptada con cambio de fecha'),
        ('ACWP', 'Aceptada con cambio de hora'),
        ('ACCC', 'Aceptada con cambio de contrato'),
        ('CANC', 'Cancelada'),
        ('PDNG', 'Pendiente')
    ]

    payment = models.ForeignKey(SepaCreditTransfer, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Estado de Transferencia SEPA'
        verbose_name_plural = 'Estados de Transferencias SEPA'
        ordering = ['-timestamp']

    def __str__(self):
        return f'Estado {self.status} para transferencia {self.payment.payment_id}'

class SepaCreditTransferDetails(models.Model):
    """
    Almacena una copia completa de los detalles de la transferencia.
    Útil para auditoría y respaldo.
    """
    payment = models.OneToOneField(SepaCreditTransfer, on_delete=models.CASCADE, related_name='details')
    auth_id = models.CharField(max_length=50)
    transaction_status = models.CharField(max_length=10)
    purpose_code = models.CharField(max_length=4)
    requested_execution_date = models.DateField()
    debtor_name = models.CharField(max_length=140)
    debtor_iban = models.CharField(max_length=34, validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')])
    debtor_currency = models.CharField(max_length=3)
    creditor_name = models.CharField(max_length=70)
    creditor_iban = models.CharField(max_length=34, validators=[RegexValidator(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')])
    creditor_currency = models.CharField(max_length=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    end_to_end_id = models.CharField(max_length=35)
    instruction_id = models.CharField(max_length=35)
    remittance_structured = models.CharField(max_length=140, null=True, blank=True)
    remittance_unstructured = models.CharField(max_length=140, null=True, blank=True)

    class Meta:
        verbose_name = 'Detalles de Transferencia SEPA'
        verbose_name_plural = 'Detalles de Transferencias SEPA'

    def __str__(self):
        return f'Detalles de transferencia {self.payment.payment_id}'

class SepaCreditTransferError(models.Model):
    """
    Registra errores durante el proceso de transferencia.
    """
    ERROR_CODES = {
        2: 'Valor inválido',
        114: 'No se puede identificar la transacción',
        121: 'Respuesta de desafío OTP inválida',
        122: 'OTP inválido',
        127: 'La fecha de inicio debe preceder a la fecha final',
        131: 'Valor inválido para sortBy',
        132: 'No soportado',
        138: 'Se inició un desafío no pushTAN',
        139: 'Se inició un desafío pushTAN',
        6500: 'Parámetros incorrectos',
        6501: 'Detalles bancarios inválidos',
        6502: 'La moneda EUR es la única aceptada',
        6503: 'Parámetros faltantes o inválidos',
        6505: 'Fecha de ejecución inválida',
        6507: 'No se permite la cancelación',
        6509: 'El parámetro no coincide con el último Auth ID',
        6510: 'El estado actual no permite la actualización del segundo factor',
        6511: 'Fecha de ejecución inválida',
        6515: 'Tipo de cuenta origen inválido',
        6516: 'No se permite la cancelación',
        6517: 'La moneda EUR es la única aceptada para el acreedor',
        6518: 'La fecha solicitada no puede ser un día festivo o fin de semana',
        6519: 'La fecha de ejecución no debe ser mayor a 90 días en el futuro',
        6520: 'El formato de fecha debe ser yyyy-MM-dd',
        6521: 'La moneda EUR es la única aceptada para el deudor',
        6523: 'No hay entidad legal presente para el IBAN origen',
        6524: 'Se ha alcanzado el límite máximo permitido para el día'
    }

    payment = models.ForeignKey(SepaCreditTransfer, on_delete=models.CASCADE, related_name='errors')
    error_code = models.IntegerField()
    error_message = models.TextField()
    message_id = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Error de Transferencia SEPA'
        verbose_name_plural = 'Errores de Transferencias SEPA'
        ordering = ['-timestamp']

    def __str__(self):
        return f'Error {self.error_code} para transferencia {self.payment.payment_id}'

    @property
    def error_description(self):
        return self.ERROR_CODES.get(self.error_code, 'Descripción de error no encontrada')