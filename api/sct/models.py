import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


class TransactionStatus(models.TextChoices):
    RJCT = "RJCT", "Rejected"
    RCVD = "RCVD", "Received"
    ACCP = "ACCP", "Accepted"
    ACTC = "ACTC", "Accepted Technical Validation"
    ACSP = "ACSP", "Accepted Settlement in Process"
    ACSC = "ACSC", "Accepted Settlement Completed"
    ACWC = "ACWC", "Accepted with Change"
    ACWP = "ACWP", "Accepted with Pending"
    ACCC = "ACCC", "Accepted Credit Check"
    CANC = "CANC", "Cancelled"
    PDNG = "PDNG", "Pending"


class Action(models.TextChoices):
    CREATE = "CREATE", "Create"
    CANCEL = "CANCEL", "Cancel"

STATUS = [
    ('RJCT', 'RJCT'),
    ('RCVD', 'RCVD'),
    ('ACCP', 'ACCP'),
    ('ACTP', 'ACTP'),
    ('ACSP', 'ACSP'),
    ('ACWC', 'ACWC'),
    ('ACWP', 'ACWP'),
    ('ACCC', 'ACCC'),
    ('CANC', 'CANC'),
    ('PDNG', 'PDNG'),
]


NAME = [
    ('---', '---'),
    ('MIRYA TRADING CO LTD', 'MIRYA TRADING CO LTD'),
    ('ZAIBATSUS.L.', 'ZAIBATSUS.L.'),
    ('ELIZABETH GARDEN GROUP S.L.', 'ELIZABETH GARDEN GROUP S.L.'),
    ('REVSTAR GLOBAL INTERNATIONAL LTD', 'REVSTAR GLOBAL INTERNATIONAL LTD'),
    ('ECLIPS CORPORATION LTD.', 'ECLIPS CORPORATION LTD.'),
    ('CDG SYSTEM LTD', 'CDG SYSTEM LTD'),
    ('BFP FINANCE SERVICE S.L.', 'BFP FINANCE SERVICE S.L.'),
    ('MOHAMMAD REZA NAJAFI KALASHI', 'MOHAMMAD REZA NAJAFI KALASHI'),
    ('SERVICES ET PUBLICITÉ ONLINE LTD', 'SERVICES ET PUBLICITÉ ONLINE LTD'),
    ('XXX', 'XXX'),

]


IBAN = [
    ('---', '---'),
    ('DE86500700100925993805', 'DE86500700100925993805'),
    ('ES3901821250410201520178', 'ES3901821250410201520178'),
    ('ES7901824036500201650056', 'ES7901824036500201650056'),
    ('GB69BUKB20041558708288', 'GB69BUKB20041558708288'),
    ('GB43HBUK40127669998520', 'GB43HBUK40127669998520'),
    ('DE64202208000053288296', 'DE64202208000053288296'),
    ('ES5868880001643861269006', 'ES5868880001643861269006'),
    ('DE41400501500154813455', 'DE41400501500154813455'),
    ('GB33REVO00996939552283', 'GB33REVO00996939552283'),
    ('XXX', 'XXX'),

]


BIC = [
    ('---', '---'),
    ('DEUTDEFFXXX', 'DEUTDEFFXXX'),
    ('BBVAESMMXXX', 'BBVAESMMXXX'),
    ('BUKBGB22XXX', 'BUKBGB22XXX'),
    ('HBUKGB4BXXX', 'HBUKGB4BXXX'),
    ('SXPYDEHHXXX', 'SXPYDEHHXXX'),
    ('QNTOESB2XXX', 'QNTOESB2XXX'),
    ('WELADED1MST', 'WELADED1MST'),
    ('REVOGB21XXX', 'REVOGB21XXX'),
    ('XXX', 'XXX'),

]


BANK = [
    ('---', '---'),
    ('DEUTSCHE BANK AG', 'DEUTSCHE BANK AG'),
    ('BANCO BILBAO VIZCAYA ARGENTARIA S.A.', 'BANCO BILBAO VIZCAYA ARGENTARIA S.A.'),
    ('BARCLAYS BANK UK PLC', 'BARCLAYS BANK UK PLC'),
    ('HSBC UK BANK PLC', 'HSBC UK BANK PLC'),
    ('BANKING CIRCLE', 'BANKING CIRCLE'),
    ('OLINDA SAS SUCURSAL EN ESPAÑA', 'OLINDA SAS SUCURSAL EN ESPAÑA'),
    ('SPARKASSE MÜNSTERLAND OST', 'SPARKASSE MÜNSTERLAND OST'),
    ('REVOLUT LIMITED', 'REVOLUT LIMITED'),
    ('XXX', 'XXX'),

]


STREETNUMBER = [
    ('---', '---'),
    ('TAUNUSANLAGE 12', 'TAUNUSANLAGE 12'),
    ('CALLE IPARRAGUIRRE 20', 'CALLE IPARRAGUIRRE 20'),
    ('CALLE GENERAL RICARDOS 12 PLANTA 4, PUERTA E', 'CALLE GENERAL RICARDOS 12 PLANTA 4, PUERTA E'),
    ('PAVILION DR BARCLAYCARD HOUSE', 'PAVILION DR BARCLAYCARD HOUSE'),
    ('CENTENARY SQUARE 1', 'CENTENARY SQUARE 1'),
    ('MAXIMILIANSTRASSE 54', 'MAXIMILIANSTRASSE 54'),
    ('PZ CATALUNYA NUM.1', 'PZ CATALUNYA NUM.1'),
    ('WESELER STRABE 230', 'WESELER STRABE 230'),
    ('WESTFERRY CIRCUS 7', 'WESTFERRY CIRCUS 7'),
    ('XXX', 'XXX'),

]


ZIPCODECITY = [
    ('---', '---'),
    ('60325 FRANKFURT', '60325 FRANKFURT'),
    ('48009 BILBAO', '48009 BILBAO'),
    ('28012 MADRID', '28012 MADRID'),
    ('NN4 75G NORTHAMPTON', 'NN4 75G NORTHAMPTON'),
    ('B1 1HQ BIRMINGHAM', 'B1 1HQ BIRMINGHAM'),
    ('80538 MÜNCHEN', '80538 MÜNCHEN'),
    ('08850 GAVA', '08850 GAVA'),
    ('48151 MÜNSTER', '48151 MÜNSTER'),
    ('E14 4HD LONDON', 'E14 4HD LONDON'),
    ('XXX', 'XXX'),

]


COUNTRY = [
    ('--', '--'),
    ('DE', 'Germany'),
    ('ES', 'Spain'),
    ('GB', 'Great Britain'),
    ('UK', 'United Kingdom'),
    ('FR', 'France'),

]


CURRENCYCODE = [
    ('---', '---'),
    ('EUR', 'EUR'),
    ('GBP', 'GBP'),
    ('USD', 'USD'),
    ('JPY', 'JPY'),
]





class SepaCreditTransferRequest(models.Model):
    idempotency_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    transaction_status = models.CharField(max_length=10, choices=STATUS, default="PDNG")
    purpose_code = models.CharField(max_length=4, blank=True, null=True, default="INST")
    
    payment_id = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    auth_id = models.UUIDField(default=uuid.uuid4, editable=True, unique=True)
    
    requested_execution_date = models.DateField(auto_now_add=True ,blank=True, null=True)
    
    debtor_name = models.CharField(max_length=140, choices=NAME, default="MIRYA TRADING CO LTD")
    debtor_adress_street_and_house_number = models.CharField(max_length=70, choices=STREETNUMBER, default="TAUNUSANLAGE 12")
    debtor_adress_zip_code_and_city = models.CharField(max_length=70, choices=ZIPCODECITY, default="60325 FRANKFURT")
    debtor_adress_country = models.CharField(max_length=2, choices=COUNTRY, default="DE")
    debtor_account_iban = models.CharField(max_length=34, choices=IBAN, default="DE86500700100925993805")
    debtor_account_bic = models.CharField(max_length=11, choices=BIC, default="DEUTDEFFXXX")
    debtor_account_currency = models.CharField(max_length=3, choices=CURRENCYCODE, default="EUR")
    
    payment_identification_end_to_end_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    payment_identification_instruction_id = models.CharField(max_length=35, blank=True, null=True)
        
    instructed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    instructed_currency = models.CharField(max_length=3, choices=CURRENCYCODE)
        
    creditor_name = models.CharField(max_length=70, choices=NAME, default="")
    creditor_adress_street_and_house_number = models.CharField(max_length=70, choices=STREETNUMBER, default="")
    creditor_adress_zip_code_and_city = models.CharField(max_length=70, choices=ZIPCODECITY, default="")
    creditor_adress_country = models.CharField(max_length=2, choices=COUNTRY, default="")    
    creditor_account_iban = models.CharField(max_length=34, choices=IBAN, default="")
    creditor_account_bic = models.CharField(max_length=11, choices=BIC, default="")
    creditor_account_currency = models.CharField(max_length=3, choices=CURRENCYCODE, default="")
    creditor_agent_financial_institution_id = models.CharField(max_length=255, choices=BANK, default="")
    
    remittance_information_structured = models.CharField(max_length=10, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return str(self.idempotency_key)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Request"
        verbose_name_plural = "SEPA Credit Transfer Requests"


@receiver(pre_save, sender=SepaCreditTransferRequest)
def set_default_fields(sender, instance, **kwargs):
    try:
        if not instance.payment_identification_end_to_end_id:
            instance.payment_identification_end_to_end_id = uuid.uuid4()
        if not instance.idempotency_key:
            instance.idempotency_key = uuid.uuid4()
        if not instance.payment_id:
            instance.payment_id = uuid.uuid4()
        if not instance.auth_id:
            instance.auth_id = uuid.uuid4()
        logger.info(f"Campos predeterminados establecidos para la transferencia {instance.id}")
    except Exception as e:
        logger.error(f"Error al establecer campos predeterminados: {str(e)}", exc_info=True)
        raise


class SepaCreditTransferUpdateScaRequest(models.Model):
    action = models.CharField(max_length=10, choices=Action.choices)
    auth_id = models.UUIDField()
    payment_id = models.ForeignKey(SepaCreditTransferRequest, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.payment_id)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Update SCA Request"
        verbose_name_plural = "SEPA Credit Transfer Update SCA Requests"


class SepaCreditTransferResponse(models.Model):
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices)
    payment_id = models.ForeignKey(SepaCreditTransferRequest, on_delete=models.CASCADE)
    auth_id = models.UUIDField()
    
    def __str__(self):
        return str(self.payment_id)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Response"
        verbose_name_plural = "SEPA Credit Transfer Responses"


class SepaCreditTransferDetailsResponse(models.Model):
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices)
    payment_id = models.ForeignKey(SepaCreditTransferRequest, on_delete=models.CASCADE)
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
    requested_execution_date = models.DateField(blank=True, null=True)
    
    debtor_name = models.CharField(max_length=140)
    debtor_adress_street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    debtor_adress_zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)
    debtor_adress_country = models.CharField(max_length=2)    
    debtor_account_iban = models.CharField(max_length=34)
    debtor_account_bic = models.CharField(max_length=11)
    debtor_account_currency = models.CharField(max_length=3)
    
    creditor_name = models.CharField(max_length=70)
    creditor_adress_street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    creditor_adress_zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)
    creditor_adress_country = models.CharField(max_length=2)    
    creditor_account_iban = models.CharField(max_length=34)
    creditor_account_bic = models.CharField(max_length=11)
    creditor_account_currency = models.CharField(max_length=3)  # Corregido de "creditot_account_currency"
    creditor_agent_financial_institution_id = models.CharField(max_length=255)
    
    payment_identification_end_to_end_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    payment_identification_instruction_id = models.CharField(max_length=35, blank=True, null=True)
        
    instructed_amount = models.DecimalField(max_digits=15, decimal_places=2)
    instructed_currency = models.CharField(max_length=3)
        
    remittance_information_structured = models.CharField(max_length=140, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)
    
    def __str__(self):
        return str(self.payment_id)
    
    class Meta:
        verbose_name = "SEPA Credit Transfer Details Response"
        verbose_name_plural = "SEPA Credit Transfer Details Responses"


class ErrorResponse(models.Model):
    code = models.IntegerField()
    message = models.CharField(max_length=170, blank=True, null=True)
    message_id = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.code} - {self.message_id} - {self.message}"
    
    class Meta:
        verbose_name = "Error Response"
        verbose_name_plural = "Error Responses"



class CategoryPurpose(models.Model):
    code = models.CharField(max_length=4, help_text="Category purpose code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)
    
    class Meta:
        verbose_name = "Category Purpose"
        verbose_name_plural = "Category Purposes"


class ServiceLevel(models.Model):
    code = models.CharField(max_length=4, help_text="Service level code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)
    
    class Meta:
        verbose_name = "Service Level"
        verbose_name_plural = "Service Levels"


class LocalInstrument(models.Model):
    code = models.CharField(max_length=4, help_text="Local instrument code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)
    
    class Meta:
        verbose_name = "Local Instrument"
        verbose_name_plural = "Local Instruments"
