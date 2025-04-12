from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generar_pdf_transferencia(transfer_request):
    """
    Generates a well-organized PDF with SEPA transfer details.
    """
    # PDF file name
    creditor_name = transfer_request.creditor_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transfer_request.payment_id
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
        ["Payment Reference", transfer_request.payment_id],
        ["Idempotency Key", transfer_request.idempotency_key]
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
        ["Name", transfer_request.debtor_name],
        ["IBAN", transfer_request.debtor_account_iban],
        ["BIC", transfer_request.debtor_account_bic],
        ["Address", f"{transfer_request.debtor_adress_street_and_house_number}, "
                    f"{transfer_request.debtor_adress_zip_code_and_city}, {transfer_request.debtor_adress_country}"]
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
        ["Name", transfer_request.creditor_name],
        ["IBAN", transfer_request.creditor_account_iban],
        ["BIC", transfer_request.creditor_account_bic],
        ["Address", f"{transfer_request.creditor_adress_street_and_house_number}, "
                    f"{transfer_request.creditor_adress_zip_code_and_city}, {transfer_request.creditor_adress_country}"]
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
        ["Amount", f"{transfer_request.instructed_amount} {transfer_request.instructed_currency}"],
        ["Requested Execution Date", transfer_request.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transfer_request.purpose_code],
        ["Remittance Information (Structured)", transfer_request.remittance_information_structured or 'N/A'],
        ["Remittance Information (Unstructured)", transfer_request.remittance_information_unstructured or 'N/A'],
        ["Auth ID", transfer_request.auth_id],
        ["Transaction Status", transfer_request.transaction_status],
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

    return pdf_path