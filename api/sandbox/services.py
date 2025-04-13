"""
Service functions for the Sandbox application.

This module provides utilities for simulating banking operations
without requiring actual bank connections, suitable for testing
and development environments.
"""
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException, Timeout, ConnectionError
import uuid

from api.sandbox.models import IncomingCollection, SandboxBankAccount, SandboxTransaction


# Configure logger
logger = logging.getLogger(__name__)


def process_incoming_collection(data: Dict[str, Any]) -> IncomingCollection:
    """
    Process an incoming collection and save it to the database.
    
    This function simulates receiving a collection request from a banking system.
    
    Args:
        data: Collection data including amount, reference, sender, etc.
        
    Returns:
        IncomingCollection: The created collection record
        
    Raises:
        ValueError: If required fields are missing
    """
    logger.info(f"Processing incoming collection: {data.get('reference_id', 'unknown')}")
    
    # Ensure required fields are present
    required_fields = ['reference_id', 'amount', 'currency', 'sender_name', 'sender_iban', 'recipient_iban']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        error_msg = f"Missing required fields: {', '.join(missing_fields)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Create the collection record
        collection = IncomingCollection.objects.create(**data)
        
        # Simulate sandbox behavior: randomly complete or keep pending
        # In a real system, this would depend on actual processing logic
        if random.random() < 0.7:  # 70% chance of completion
            collection.status = "COMPLETED"
            collection.save(update_fields=['status'])
            logger.info(f"Collection {collection.reference_id} completed")
        else:
            logger.info(f"Collection {collection.reference_id} pending for manual review")
        
        return collection
    
    except Exception as e:
        logger.error(f"Error processing incoming collection: {str(e)}", exc_info=True)
        raise


def get_account_balance(account_id: str) -> Dict[str, Any]:
    """
    Get account balance from Deutsche Bank (or sandbox).
    
    This function simulates retrieving account balance information.
    In a sandbox environment, it returns simulated data rather than
    making actual API calls.
    
    Args:
        account_id: The ID of the account to query
        
    Returns:
        Dict[str, Any]: Account balance information or error
    """
    logger.info(f"Getting balance for account: {account_id}")
    
    try:
        # Check if we have this account in our sandbox
        account = SandboxBankAccount.objects.filter(account_number=account_id).first()
        
        # If we have a sandbox account, return its balance
        if account:
            logger.info(f"Using sandbox account data for {account_id}")
            return {
                "account_id": account_id,
                "balance": str(account.balance),
                "currency": account.currency,
                "timestamp": timezone.now().isoformat(),
                "is_sandbox": True
            }
            
        # Otherwise, attempt to call the real API (in production) or simulate (in development)
        if settings.USE_REAL_BANK_APIS and not settings.DEBUG:
            url = f"{settings.DEUTSCHE_BANK_API_URL}/accounts/{account_id}/balance"
            response = requests.get(
                url, 
                headers={"Authorization": f"Bearer {settings.DEUTSCHE_BANK_API_KEY}"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            
            logger.error(f"Error from Deutsche Bank API: {response.status_code} - {response.text}")
            return {"error": f"Failed to get balance: {response.status_code}"}
        
        # Simulate response in development/sandbox mode
        logger.info(f"Simulating balance response for {account_id}")
        return {
            "account_id": account_id,
            "balance": str(random.uniform(1000, 10000)),
            "currency": "EUR",
            "timestamp": timezone.now().isoformat(),
            "is_sandbox": True
        }
    
    except RequestException as e:
        logger.error(f"Request error getting account balance: {str(e)}")
        return {"error": f"Connection error: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Unexpected error getting account balance: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def initiate_sepa_transfer(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a SEPA transfer with Deutsche Bank.
    
    This function simulates initiating a SEPA transfer. In sandbox mode,
    it creates a simulated transaction rather than making actual transfers.
    
    Args:
        data: Transfer data including amount, sender, recipient, etc.
        
    Returns:
        Dict[str, Any]: Transfer result or error information
    """
    logger.info(f"Initiating SEPA transfer: {data}")
    
    try:
        # Validate required fields
        required_fields = ['amount', 'currency', 'sender_iban', 'recipient_iban', 'sender_name', 'recipient_name']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Generate a unique transaction ID if not provided
        transaction_id = data.get('transaction_id', str(uuid.uuid4()))
        
        # Check if this is a sandbox mode or real API mode
        if settings.USE_REAL_BANK_APIS and not settings.DEBUG:
            # Call the real API
            url = f"{settings.DEUTSCHE_BANK_API_URL}/sepa/transfer"
            response = requests.post(
                url, 
                json=data,
                headers={"Authorization": f"Bearer {settings.DEUTSCHE_BANK_API_KEY}"},
                timeout=30
            )
            
            if response.status_code == 201:
                return response.json()
                
            logger.error(f"Error from Deutsche Bank API: {response.status_code} - {response.text}")
            return {"error": f"Failed to initiate transfer: {response.status_code}"}
        
        # Sandbox mode: simulate transfer
        logger.info("Using sandbox mode for SEPA transfer")
        
        # Simulate processing delay
        time.sleep(random.uniform(0.5, 2.0))
        
        # Find or create sandbox accounts
        sender_account, _ = SandboxBankAccount.objects.get_or_create(
            account_number=data['sender_iban'],
            defaults={
                'account_holder': data['sender_name'],
                'currency': data['currency'],
                'balance': max(Decimal(data['amount']) * 2, Decimal('1000.00'))  # Ensure sufficient funds
            }
        )
        
        recipient_account, _ = SandboxBankAccount.objects.get_or_create(
            account_number=data['recipient_iban'],
            defaults={
                'account_holder': data['recipient_name'],
                'currency': data['currency'],
                'balance': Decimal('0.00')
            }
        )
        
        # Create a sandbox transaction
        transaction = SandboxTransaction.objects.create(
            transaction_id=transaction_id,
            from_account=sender_account,
            to_account=recipient_account,
            amount=data['amount'],
            currency=data['currency'],
            description=data.get('description', 'SEPA Transfer'),
            status="PENDING"
        )
        
        # Process the transaction (transfer the funds in the sandbox)
        success = transaction.process()
        
        if success:
            return {
                "transaction_id": transaction.transaction_id,
                "status": "COMPLETED",
                "sender_iban": sender_account.account_number,
                "recipient_iban": recipient_account.account_number,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "timestamp": timezone.now().isoformat(),
                "is_sandbox": True
            }
        else:
            return {
                "transaction_id": transaction.transaction_id,
                "status": "FAILED",
                "error": transaction.error_message,
                "is_sandbox": True
            }
    
    except Exception as e:
        logger.error(f"Error initiating SEPA transfer: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def approve_collection(collection_id: str, approve: bool, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Approve or reject an incoming collection.
    
    Args:
        collection_id: The ID of the collection to approve/reject
        approve: True to approve, False to reject
        reason: Reason for rejection (required if rejecting)
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    logger.info(f"{'Approving' if approve else 'Rejecting'} collection {collection_id}")
    
    try:
        collection = IncomingCollection.objects.get(id=collection_id)
        
        if approve:
            if collection.approve():
                return {
                    "success": True,
                    "collection_id": collection_id,
                    "status": "COMPLETED",
                    "message": "Collection approved successfully"
                }
            else:
                return {
                    "success": False,
                    "collection_id": collection_id,
                    "message": f"Cannot approve collection with status {collection.status}"
                }
        else:
            if reason is None:
                return {
                    "success": False,
                    "collection_id": collection_id,
                    "message": "Reason is required for rejection"
                }
                
            if collection.reject(reason):
                return {
                    "success": True,
                    "collection_id": collection_id,
                    "status": "REJECTED",
                    "message": "Collection rejected successfully"
                }
            else:
                return {
                    "success": False,
                    "collection_id": collection_id,
                    "message": f"Cannot reject collection with status {collection.status}"
                }
    
    except IncomingCollection.DoesNotExist:
        logger.error(f"Collection {collection_id} not found")
        return {
            "success": False,
            "message": f"Collection {collection_id} not found"
        }
        
    except Exception as e:
        logger.error(f"Error approving/rejecting collection: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }


def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
    """
    Get the status of a transaction.
    
    Args:
        transaction_id: The ID of the transaction to check
        
    Returns:
        Dict[str, Any]: Transaction status information
    """
    logger.info(f"Checking status of transaction {transaction_id}")
    
    try:
        transaction = SandboxTransaction.objects.get(transaction_id=transaction_id)
        
        return {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "from_account": transaction.from_account.account_number,
            "to_account": transaction.to_account.account_number,
            "amount": str(transaction.amount),
            "currency": transaction.currency,
            "timestamp": transaction.created_at.isoformat(),
            "description": transaction.description,
            "error_message": transaction.error_message,
            "is_sandbox": True
        }
        
    except SandboxTransaction.DoesNotExist:
        logger.error(f"Transaction {transaction_id} not found")
        return {"error": f"Transaction {transaction_id} not found"}
        
    except Exception as e:
        logger.error(f"Error checking transaction status: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}