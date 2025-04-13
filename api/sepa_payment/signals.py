"""
Signal handlers for SEPA payment models.

This module defines Django signal handlers that react to model save events
to automatically create related objects and perform necessary updates.
"""
from datetime import datetime
from typing import Any, Dict, Type

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from api.sepa_payment.models import (
    SepaCreditTransfer, 
    SepaCreditTransferDetails, 
    SepaCreditTransferStatus
)


@receiver(post_save, sender=SepaCreditTransfer)
def create_transfer_details(
    sender: Type[SepaCreditTransfer], 
    instance: SepaCreditTransfer, 
    created: bool, 
    **kwargs: Any
) -> None:
    """
    Create a detailed record when a new SEPA credit transfer is created.
    
    This signal handler creates a SepaCreditTransferDetails record that contains
    a copy of all the payment details for historical and reporting purposes.
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created: A boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        try:
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
        except Exception as e:
            # Log the error but don't prevent the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating transfer details for {instance.payment_id}: {str(e)}", exc_info=True)


@receiver(post_save, sender=SepaCreditTransfer)
def create_initial_status(
    sender: Type[SepaCreditTransfer], 
    instance: SepaCreditTransfer, 
    created: bool, 
    **kwargs: Any
) -> None:
    """
    Create an initial status record when a new SEPA credit transfer is created.
    
    This signal handler creates a SepaCreditTransferStatus record with the
    initial 'PDNG' (Pending) status for a new payment.
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created: A boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        try:
            SepaCreditTransferStatus.objects.create(
                payment=instance,
                status='PDNG',  # Pending status
                timestamp=timezone.now()
            )
        except Exception as e:
            # Log the error but don't prevent the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating initial status for {instance.payment_id}: {str(e)}", exc_info=True)


@receiver(post_save, sender=SepaCreditTransferStatus)
def update_transfer_status(
    sender: Type[SepaCreditTransferStatus], 
    instance: SepaCreditTransferStatus, 
    created: bool, 
    **kwargs: Any
) -> None:
    """
    Update the main transfer record when a new status is recorded.
    
    This signal handler updates the transaction_status field on the
    SepaCreditTransfer model whenever a new status is recorded.
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created: A boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        try:
            # Update the main payment record with the latest status
            payment = instance.payment
            payment.transaction_status = instance.status
            payment.save(update_fields=['transaction_status'])
        except Exception as e:
            # Log the error but don't prevent the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating transfer status for {instance.payment.payment_id}: {str(e)}", exc_info=True)


@receiver(post_save, sender=SepaCreditTransfer)
def handle_status_changes(
    sender: Type[SepaCreditTransfer], 
    instance: SepaCreditTransfer, 
    created: bool, 
    **kwargs: Any
) -> None:
    """
    Perform actions based on payment status changes.
    
    This signal handler responds to status changes on SepaCreditTransfer
    records to trigger appropriate actions (like notifications).
    
    Args:
        sender: The model class that sent the signal
        instance: The actual instance being saved
        created: A boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Skip processing for new records (initial status is handled by create_initial_status)
    if not created:
        try:
            # Get the previous state from kwargs if available
            previous_status = None
            if 'update_fields' in kwargs and 'transaction_status' in kwargs['update_fields']:
                # Try to get previous status from history if available
                statuses = SepaCreditTransferStatus.objects.filter(
                    payment=instance
                ).order_by('-timestamp')
                
                if len(statuses) >= 2:
                    previous_status = statuses[1].status

            current_status = instance.transaction_status
            
            # If we detect a status change
            if previous_status and previous_status != current_status:
                # Here you could trigger notifications or other status-dependent actions
                pass
                
        except Exception as e:
            # Log the error but don't prevent the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error handling status change for {instance.payment_id}: {str(e)}", exc_info=True)