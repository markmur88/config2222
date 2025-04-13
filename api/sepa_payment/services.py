"""
Services for SEPA payment processing.

This module provides service classes for interacting with SEPA payment APIs,
handling authentication, payment creation, and status tracking.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from api.sepa_payment.models import SepaCreditTransfer, SepaCreditTransferError, SepaCreditTransferStatus


# Configure logger
logger = logging.getLogger(__name__)


class SepaPaymentService:
    """
    Service for handling SEPA credit transfer operations.
    
    This class provides methods for authenticating with the API,
    creating payments, and checking payment statuses.
    """
    
    def __init__(self):
        """
        Initialize the SEPA payment service with API credentials.
        
        Raises:
            ImproperlyConfigured: If required API settings are missing
        """
        self.api_base_url = getattr(settings, 'API_BASE_URL', None)
        self.client_id = getattr(settings, 'API_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'API_CLIENT_SECRET', None)
        self.access_token = None
        
        # Validate required settings
        if not all([self.api_base_url, self.client_id, self.client_secret]):
            raise ImproperlyConfigured('Missing environment variables for API configuration')
    
    def _get_access_token(self) -> str:
        """
        Obtain an OAuth2 access token for API authentication.
        
        Returns:
            str: The access token
            
        Raises:
            Exception: If authentication fails
        """
        if not self.access_token:
            try:
                auth_url = f"{self.api_base_url}/oauth2/token"
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                }
                
                response = requests.post(auth_url, headers=headers, data=data, timeout=30)
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data['access_token']
                logger.info("Successfully obtained API access token")
            
            except requests.exceptions.RequestException as e:
                error_msg = f"Error obtaining API token: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise Exception(error_msg)
        
        return self.access_token
    
    def create_payment(self, data: Dict[str, Any]) -> str:
        """
        Create a SEPA credit transfer payment.
        
        Args:
            data: Dictionary containing payment details
            
        Returns:
            str: The payment ID of the created payment
            
        Raises:
            Exception: If payment creation fails
        """
        try:
            # Get authentication token
            access_token = self._get_access_token()
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Request-ID': self._generate_request_id(),
                'PSU-ID': '02569S',  # User ID
                'PSU-IP-Address': '193.150.166.1'  # User IP address
            }
            
            # Prepare payment payload
            payload = {
                'purposeCode': data['purpose_code'],
                'requestedExecutionDate': data['requested_execution_date'].strftime('%Y-%m-%d'),
                'debtor': {
                    'name': data['debtor_name'],
                    'postalAddress': {
                        'country': data['debtor_address_country'],
                        'addressLine': [
                            f"{data['debtor_address_street']}, {data['debtor_address_zip']}"
                        ]
                    }
                },
                'debtorAccount': {
                    'iban': data['debtor_iban'],
                    'currency': data['debtor_currency']
                },
                'paymentIdentification': {
                    'endToEndId': data['end_to_end_id'],
                    'instructionId': data['instruction_id']
                },
                'instructedAmount': {
                    'amount': str(data['amount']),
                    'currency': data['creditor_currency']
                },
                'creditorAgent': {
                    'financialInstitutionId': data['creditor_agent_id']
                },
                'creditor': {
                    'name': data['creditor_name'],
                    'postalAddress': {
                        'country': data['creditor_address_country'],
                        'addressLine': [
                            f"{data['creditor_address_street']}, {data['creditor_address_zip']}"
                        ]
                    }
                },
                'creditorAccount': {
                    'iban': data['creditor_iban'],
                    'currency': data['creditor_currency']
                },
                'remittanceInformationStructured': data['remittance_structured'],
                'remittanceInformationUnstructured': data['remittance_unstructured']
            }
            
            # Send request to API
            response = requests.post(
                self.api_base_url, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            # Process response
            if response.status_code == 201:
                payment_id = response.json()['paymentId']
                logger.info(f"Successfully created payment with ID: {payment_id}")
                return payment_id
            else:
                error_msg = f"Error creating payment: {response.text} (Status: {response.status_code})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Payment creation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get the status of a SEPA credit transfer payment.
        
        Args:
            payment_id: The ID of the payment to check
            
        Returns:
            Dict[str, Any]: The payment status information
            
        Raises:
            Exception: If status retrieval fails
        """
        try:
            # Get authentication token
            access_token = self._get_access_token()
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Request-ID': self._generate_request_id()
            }
            
            # Send request to API
            response = requests.get(
                f"{self.api_base_url}/{payment_id}/status",
                headers=headers,
                timeout=30
            )
            
            # Process response
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"Successfully retrieved status for payment {payment_id}")
                return status_data
            else:
                error_msg = f"Error retrieving payment status: {response.text} (Status: {response.status_code})"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            error_msg = f"Payment status retrieval failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        """
        Update the status of a payment and record the change.
        
        Args:
            payment_id: The ID of the payment to update
            status: The new status to set
            
        Returns:
            bool: True if the update was successful
            
        Raises:
            Exception: If the payment is not found or update fails
        """
        try:
            # Find the payment
            payment = SepaCreditTransfer.objects.get(payment_id=payment_id)
            
            # Create status record
            SepaCreditTransferStatus.objects.create(
                payment=payment,
                status=status,
                timestamp=timezone.now()
            )
            
            logger.info(f"Successfully updated payment {payment_id} status to {status}")
            return True
            
        except SepaCreditTransfer.DoesNotExist:
            error_msg = f"Payment with ID {payment_id} not found"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Error updating payment status: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._log_error(payment_id, error_msg)
            raise Exception(error_msg)
    
    def _log_error(self, payment_id: str, error_message: str) -> None:
        """
        Record an error in the database.
        
        Args:
            payment_id: The ID of the payment related to the error
            error_message: The error message to record
        """
        try:
            # Try to find the payment
            try:
                payment = SepaCreditTransfer.objects.get(payment_id=payment_id)
                
                # Create error record with payment reference
                SepaCreditTransferError.objects.create(
                    payment=payment,
                    error_code=999,  # Generic code for internal errors
                    error_message=error_message,
                    message_id=self._generate_message_id(),
                    timestamp=timezone.now()
                )
                
            except SepaCreditTransfer.DoesNotExist:
                # If payment not found, create error without payment reference
                SepaCreditTransferError.objects.create(
                    payment_id=payment_id,
                    error_code=999,
                    error_message=error_message,
                    message_id=self._generate_message_id(),
                    timestamp=timezone.now()
                )
                
            logger.info(f"Error logged for payment {payment_id}")
            
        except Exception as e:
            logger.error(f"Failed to log error: {str(e)}", exc_info=True)
    
    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID for API calls.
        
        Returns:
            str: A unique request ID
        """
        return f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    
    def _generate_message_id(self) -> str:
        """
        Generate a unique message ID for error logging.
        
        Returns:
            str: A unique message ID
        """
        return f"ERR-{timezone.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"


class SepaPaymentStatusPoller:
    """
    Service for polling payment statuses and updating them in the system.
    
    This class is used to periodically check the status of pending payments
    and update their status in the database.
    """
    
    def __init__(self):
        """Initialize the status poller with the payment service."""
        self.payment_service = SepaPaymentService()
    
    def poll_pending_payments(self) -> int:
        """
        Poll the status of all pending payments and update them.
        
        Returns:
            int: Number of payments updated
        """
        updated_count = 0
        
        try:
            # Get all payments with "PDNG" status
            pending_payments = SepaCreditTransfer.objects.filter(
                latest_status__status="PDNG"
            )
            
            for payment in pending_payments:
                try:
                    # Get latest status from API
                    status_data = self.payment_service.get_payment_status(payment.payment_id)
                    new_status = status_data.get('transactionStatus')
                    
                    # If status has changed, update it
                    if new_status and new_status != "PDNG":
                        self.payment_service.update_payment_status(payment.payment_id, new_status)
                        updated_count += 1
                        
                except Exception as e:
                    logger.error(
                        f"Error updating status for payment {payment.payment_id}: {str(e)}",
                        exc_info=True
                    )
            
            logger.info(f"Updated status for {updated_count} payments")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error polling pending payments: {str(e)}", exc_info=True)
            return updated_count