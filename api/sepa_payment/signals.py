# apps/sepa_payment/signals.py
from datetime import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.sepa_payment.models import SepaCreditTransfer, SepaCreditTransferDetails, SepaCreditTransferStatus

@receiver(post_save, sender=SepaCreditTransfer)
def create_transfer_details(sender, instance, created, **kwargs):
    if created:
        SepaCreditTransferDetails.objects.create(
            payment=instance,
            auth_id=instance.auth_id,
            transaction_status=instance.transaction_status,
            purpose_code=instance.purpose_code,
            requested_execution_date=instance.requested_execution_date,
            debtor_name=instance.debtor_name,
            debtor_iban=instance.debtor_iban,
            debtor_currency=instance.debtor_currency,
            creditor_name=instance.creditor_name,
            creditor_iban=instance.creditor_iban,
            creditor_currency=instance.creditor_currency,
            amount=instance.amount,
            end_to_end_id=instance.end_to_end_id,
            instruction_id=instance.instruction_id,
            remittance_structured=instance.remittance_structured,
            remittance_unstructured=instance.remittance_unstructured
        )

@receiver(post_save, sender=SepaCreditTransfer)
def create_initial_status(sender, instance, created, **kwargs):
    if created:
        SepaCreditTransferStatus.objects.create(
            payment=instance,
            status='PDNG',
            timestamp=timezone.now()
        )