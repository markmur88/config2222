"""
PDF generation module for SEPA Credit Transfer receipts.
Provides functionality to create well-formatted PDF documents with transaction details.
"""
import logging
import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from api.sct.models import SepaCreditTransferRequest  # Add this import for type hints

logger = logging.getLogger("bank_services")


def generar_pdf_transferencia(transfers: SepaCreditTransferRequest) -> str:
    """
    Generates a well-organized PDF with SEPA transfer details.
    
    Args:
        transfers: The SepaCreditTransferRequest object containing transfer details
        
    Returns:
        str: The path to the generated PDF file
    """
    # PDF file name
    creditor_name = transfers.creditor_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transfers.payment_id
    pdf_filename = f"{creditor_name}_{timestamp}_{payment_reference}.pdf"
    pdf_path = os.path.join("media", pdf_filename)
    
    # Create the media folder if it doesn't exist
    os.makedirs("media", exist_ok=True)
    
    # Create the PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(150, 750, "SEPA Transfer Receipt")  # Adjust title position
    c.setFont("Helvetica", 10)
    
    # Adjust initial positions
    current_y = 650  # Initial position for tables
    
    # Header
    header_data = [
        ["Creation Date", datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
        ["Payment Reference", transfers.payment_id],
        ["Idempotency Key", transfers.idempotency_key]
    ]
    header_table = Table(header_data, colWidths=[150, 300])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    header_table.wrapOn(c, 50, current_y)
    header_table.drawOn(c, 50, current_y)
    current_y -= 120  # Adjust space for the next table
    
    # Debtor Information
    debtor_data = [
        ["Debtor Information", ""],
        ["Name", transfers.debtor_name],
        ["IBAN", transfers.debtor_account_iban],
        ["BIC", transfers.debtor_account_bic],
        ["Address", f"{transfers.debtor_adress_street_and_house_number}, "
                   f"{transfers.debtor_adress_zip_code_and_city}, {transfers.debtor_adress_country}"]
    ]
    debtor_table = Table(debtor_data, colWidths=[150, 300])
    debtor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    debtor_table.wrapOn(c, 50, current_y)
    debtor_table.drawOn(c, 50, current_y)
    current_y -= 120  # Adjust space for the next table
    
    # Creditor Information
    creditor_data = [
        ["Creditor Information", ""],
        ["Name", transfers.creditor_name],
        ["IBAN", transfers.creditor_account_iban],
        ["BIC", transfers.creditor_account_bic],
        ["Address", f"{transfers.creditor_adress_street_and_house_number}, "
                   f"{transfers.creditor_adress_zip_code_and_city}, {transfers.creditor_adress_country}"]
    ]
    creditor_table = Table(creditor_data, colWidths=[150, 300])
    creditor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    creditor_table.wrapOn(c, 50, current_y)
    creditor_table.drawOn(c, 50, current_y)
    current_y -= 200  # Adjust space for the next table
    
    # Transfer Details
    transfer_data = [
        ["Transfer Details", ""],
        ["Amount", f"{transfers.instructed_amount} {transfers.instructed_currency}"],
        ["Requested Execution Date", transfers.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transfers.purpose_code],
        ["Remittance Information (Structured)", transfers.remittance_information_structured or 'N/A'],
        ["Remittance Information (Unstructured)", transfers.remittance_information_unstructured or 'N/A'],
        ["Auth ID", transfers.auth_id],
        ["Transaction Status", transfers.transaction_status],
        ["Priority", "High (Instant SEPA Credit Transfer)"]
    ]
    transfer_table = Table(transfer_data, colWidths=[200, 250])
    transfer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    transfer_table.wrapOn(c, 50, current_y)
    transfer_table.drawOn(c, 50, current_y)
    current_y -= 200  # Adjust space for the footer
    
    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "This document is an automatically generated receipt and does not require a signature.")
    
    # Save the PDF
    c.save()
    
    logger.info(f"Generated PDF receipt at {pdf_path}")
    return pdf_path