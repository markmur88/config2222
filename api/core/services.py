"""
Core services for document generation and other utilities.

This module provides utility functions for generating standardized 
SEPA XML files and PDF documents for financial transactions, as well
as other common service functions.
"""
import os
import uuid
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, Optional, Union, List

from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

# Configure logger
logger = logging.getLogger(__name__)

# Import transaction model types if available
try:
    from api.transfers.models import SEPA3
except ImportError:
    # Type fallback if model isn't available
    SEPA3 = Any


def generate_sepa_xml(transaction: Any) -> str:
    """
    Generate a SEPA XML file (ISO 20022) for a transfer transaction.
    
    Creates an XML document in the pain.001.001.03 format which is the
    standard for SEPA Credit Transfers.
    
    Args:
        transaction: The transaction object containing transfer details
        
    Returns:
        str: The generated XML as a string
    """
    try:
        # Create XML document
        root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
        CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")
        
        # Payment group information
        GrpHdr = ET.SubElement(CstmrCdtTrfInitn, "GrpHdr")
        ET.SubElement(GrpHdr, "MsgId").text = str(uuid.uuid4())  # Unique message ID
        ET.SubElement(GrpHdr, "CreDtTm").text = datetime.utcnow().isoformat()
        ET.SubElement(GrpHdr, "NbOfTxs").text = "1"
        ET.SubElement(GrpHdr, "CtrlSum").text = str(transaction.amount)
        InitgPty = ET.SubElement(GrpHdr, "InitgPty")
        ET.SubElement(InitgPty, "Nm").text = transaction.sender_name
        
        # Transaction information
        PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
        ET.SubElement(PmtInf, "PmtInfId").text = str(uuid.uuid4())
        ET.SubElement(PmtInf, "PmtMtd").text = "TRF"  # Transfer
        ET.SubElement(PmtInf, "BtchBookg").text = "false"
        ET.SubElement(PmtInf, "NbOfTxs").text = "1"
        ET.SubElement(PmtInf, "CtrlSum").text = str(transaction.amount)
        
        # Payment type information
        PmtTpInf = ET.SubElement(PmtInf, "PmtTpInf")
        SvcLvl = ET.SubElement(PmtTpInf, "SvcLvl")
        ET.SubElement(SvcLvl, "Cd").text = "SEPA"
        
        # Requested execution date
        ReqdExctnDt = ET.SubElement(PmtInf, "ReqdExctnDt")
        ReqdExctnDt.text = transaction.execution_date.strftime("%Y-%m-%d")
        
        # Debtor (sender) information
        Dbtr = ET.SubElement(PmtInf, "Dbtr")
        ET.SubElement(Dbtr, "Nm").text = transaction.sender_name
        DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
        Id = ET.SubElement(DbtrAcct, "Id")
        ET.SubElement(Id, "IBAN").text = transaction.sender_iban
        DbtrAgt = ET.SubElement(PmtInf, "DbtrAgt")
        FinInstnId = ET.SubElement(DbtrAgt, "FinInstnId")
        ET.SubElement(FinInstnId, "BIC").text = transaction.sender_bic
        
        # Creditor (recipient) information
        CdtTrfTxInf = ET.SubElement(PmtInf, "CdtTrfTxInf")
        PmtId = ET.SubElement(CdtTrfTxInf, "PmtId")
        ET.SubElement(PmtId, "EndToEndId").text = transaction.reference
        Amt = ET.SubElement(CdtTrfTxInf, "Amt")
        ET.SubElement(Amt, "InstdAmt", Ccy=transaction.currency).text = str(transaction.amount)
        CdtrAgt = ET.SubElement(CdtTrfTxInf, "CdtrAgt")
        FinInstnId = ET.SubElement(CdtrAgt, "FinInstnId")
        ET.SubElement(FinInstnId, "BIC").text = transaction.recipient_bic
        Cdtr = ET.SubElement(CdtTrfTxInf, "Cdtr")
        ET.SubElement(Cdtr, "Nm").text = transaction.recipient_name
        CdtrAcct = ET.SubElement(CdtTrfTxInf, "CdtrAcct")
        Id = ET.SubElement(CdtrAcct, "Id")
        ET.SubElement(Id, "IBAN").text = transaction.recipient_iban
        
        # Add remittance information if available
        if hasattr(transaction, 'unstructured_remittance_info') and transaction.unstructured_remittance_info:
            RmtInf = ET.SubElement(CdtTrfTxInf, "RmtInf")
            ET.SubElement(RmtInf, "Ustrd").text = transaction.unstructured_remittance_info
        
        # Generate XML string
        xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
        logger.info(f"Generated SEPA XML for transaction {getattr(transaction, 'id', 'unknown')}")
        
        return xml_string
    
    except Exception as e:
        logger.error(f"Error generating SEPA XML: {str(e)}", exc_info=True)
        raise


def generate_transfer_pdf(transfer: Any) -> str:
    """
    Generate a PDF with transaction details.
    
    Creates a professional PDF receipt for a SWIFT/SEPA transfer
    with all relevant transaction information.
    
    Args:
        transfer: The transfer object containing transaction details
        
    Returns:
        str: The path to the generated PDF file
    """
    try:
        # PDF filename
        pdf_filename = f"transfer_{getattr(transfer, 'id', uuid.uuid4())}.pdf"
        pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Set up formatting
        c.setFont("Helvetica-Bold", 14)
        c.drawString(150, 750, "SWIFT/SEPA Transfer Receipt")
        
        # Add logo if available
        # c.drawImage("path/to/logo.png", 50, 750, width=80, height=40)
        
        # Add border
        c.setStrokeColor(colors.black)
        c.rect(50, 50, letter[0] - 100, letter[1] - 100, stroke=1, fill=0)
        
        # Add transaction details
        c.setFont("Helvetica", 12)
        details = [
            f"Reference: {getattr(transfer, 'idempotency_key', 'N/A')}",
            f"Source Bank: {getattr(transfer, 'sender_bank', 'N/A')}",
            f"Source BIC: {getattr(transfer, 'sender_bic', 'N/A')}",
            f"Source IBAN: {getattr(transfer, 'sender_iban', 'N/A')}",
            f"Sender: {getattr(transfer, 'sender_name', 'N/A')}",
            f"Destination Bank: {getattr(transfer, 'recipient_bank', 'N/A')}",
            f"Destination BIC: {getattr(transfer, 'recipient_bic', 'N/A')}",
            f"Destination IBAN: {getattr(transfer, 'recipient_iban', 'N/A')}",
            f"Recipient: {getattr(transfer, 'recipient_name', 'N/A')}",
            f"Amount: {getattr(transfer, 'amount', 'N/A')} {getattr(transfer, 'currency', 'N/A')}",
            f"Status: {getattr(transfer, 'status', 'N/A')}",
            f"SWIFT/SEPA ID: {getattr(transfer, 'SEPA3_id', 'N/A')}",
            f"Date: {getattr(transfer, 'execution_date', datetime.now()).strftime('%d/%m/%Y %H:%M:%S')}",
        ]
        
        y = 700
        for detail in details:
            c.drawString(100, y, detail)
            y -= 20
        
        # Add footer
        c.setFont("Helvetica-Italic", 8)
        footer_text = "This is an official transfer receipt. Please keep for your records."
        c.drawString(100, 80, footer_text)
        
        # Add current date/time
        c.drawString(100, 70, f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Save PDF
        c.save()
        
        logger.info(f"Generated PDF for transfer {getattr(transfer, 'id', 'unknown')}")
        return pdf_path
    
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise


def validate_iban(iban: str) -> bool:
    """
    Validate an International Bank Account Number (IBAN).
    
    Performs basic validation of IBAN format and checksum.
    
    Args:
        iban: The IBAN to validate
        
    Returns:
        bool: True if IBAN is valid, False otherwise
    """
    # Remove spaces and convert to uppercase
    iban = iban.replace(' ', '').upper()
    
    # Basic format check - improve with a proper IBAN validation library
    if len(iban) < 15 or len(iban) > 34:
        return False
    
    # Move the first 4 characters to the end
    iban = iban[4:] + iban[:4]
    
    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    iban_numeric = ''
    for char in iban:
        if char.isalpha():
            iban_numeric += str(ord(char) - ord('A') + 10)
        else:
            iban_numeric += char
    
    # Check if modulo 97 equals 1
    return int(iban_numeric) % 97 == 1


def validate_bic(bic: str) -> bool:
    """
    Validate a Bank Identifier Code (BIC/SWIFT).
    
    Performs basic validation of BIC format.
    
    Args:
        bic: The BIC to validate
        
    Returns:
        bool: True if BIC is valid, False otherwise
    """
    # Remove spaces and convert to uppercase
    bic = bic.replace(' ', '').upper()
    
    # Check length (8 or 11 characters)
    if len(bic) not in [8, 11]:
        return False
    
    # Basic format check: first 4 characters should be letters (bank code)
    # Characters 5-6 should be letters (country code)
    # Characters 7-8 should be letters or digits (location code)
    # Characters 9-11 (if present) should be letters or digits (branch code)
    if not (
        bic[:4].isalpha() and
        bic[4:6].isalpha() and
        all(c.isalnum() for c in bic[6:])
    ):
        return False
    
    return True


def format_currency(amount: float, currency: str = 'EUR') -> str:
    """
    Format a currency amount with appropriate symbols and separators.
    
    Args:
        amount: The amount to format
        currency: The currency code (default: EUR)
        
    Returns:
        str: The formatted currency string
    """
    # Define currency symbols and formats
    currency_formats = {
        'EUR': ('€', '{symbol}{amount:,.2f}'),
        'USD': ('$', '{symbol}{amount:,.2f}'),
        'GBP': ('£', '{symbol}{amount:,.2f}'),
        'JPY': ('¥', '{symbol}{amount:,.0f}'),
    }
    
    # Get currency format or default to EUR
    symbol, format_string = currency_formats.get(currency, currency_formats['EUR'])
    
    # Format the amount
    return format_string.format(symbol=symbol, amount=amount)