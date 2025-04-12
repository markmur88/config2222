import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from config import settings

def generate_sepa_xml(transaction):
    """
    Genera un XML SEPA (ISO 20022) para la transferencia.
    """
    # Crear el documento XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    CstmrCdtTrfInitn = ET.SubElement(root, "CstmrCdtTrfInitn")
 
    # Información del grupo de pagos
    GrpHdr = ET.SubElement(CstmrCdtTrfInitn, "GrpHdr")
    ET.SubElement(GrpHdr, "MsgId").text = str(uuid.uuid4())  # ID único del mensaje
    ET.SubElement(GrpHdr, "CreDtTm").text = datetime.utcnow().isoformat()
    ET.SubElement(GrpHdr, "NbOfTxs").text = "1"
    ET.SubElement(GrpHdr, "CtrlSum").text = str(transaction.amount)
    InitgPty = ET.SubElement(GrpHdr, "InitgPty")
    ET.SubElement(InitgPty, "Nm").text = transaction.sender_name

    # Información de la transacción
    PmtInf = ET.SubElement(CstmrCdtTrfInitn, "PmtInf")
    ET.SubElement(PmtInf, "PmtInfId").text = str(uuid.uuid4())
    ET.SubElement(PmtInf, "PmtMtd").text = "TRF"  # Transferencia
    ET.SubElement(PmtInf, "BtchBookg").text = "false"
    ET.SubElement(PmtInf, "NbOfTxs").text = "1"
    ET.SubElement(PmtInf, "CtrlSum").text = str(transaction.amount)

    PmtTpInf = ET.SubElement(PmtInf, "PmtTpInf")
    SvcLvl = ET.SubElement(PmtTpInf, "SvcLvl")
    ET.SubElement(SvcLvl, "Cd").text = "SEPA"

    ReqdExctnDt = ET.SubElement(PmtInf, "ReqdExctnDt")
    ReqdExctnDt.text = transaction.execution_date.strftime("%Y-%m-%d")

    # Datos del ordenante
    Dbtr = ET.SubElement(PmtInf, "Dbtr")
    ET.SubElement(Dbtr, "Nm").text = transaction.sender_name

    DbtrAcct = ET.SubElement(PmtInf, "DbtrAcct")
    Id = ET.SubElement(DbtrAcct, "Id")
    ET.SubElement(Id, "IBAN").text = transaction.sender_iban

    DbtrAgt = ET.SubElement(PmtInf, "DbtrAgt")
    FinInstnId = ET.SubElement(DbtrAgt, "FinInstnId")
    ET.SubElement(FinInstnId, "BIC").text = transaction.sender_bic

    # Datos del beneficiario
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

    RmtInf = ET.SubElement(CdtTrfTxInf, "RmtInf")
    ET.SubElement(RmtInf, "Ustrd").text = transaction.unstructured_remittance_info

    # Generar el XML
    xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
    return xml_string


def generar_pdf_transferencia(transferencia):
    """
    Genera un PDF con los detalles de la transacción.
    """
    # Nombre del archivo PDF
    pdf_filename = f"transferencia_{transferencia.id}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)

    # Crear el PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Título
    c.drawString(200, 750, "Comprobante de Transferencia SWIFT")

    # Detalles de la transferencia
    detalles = [
        f"Referencia: {transferencia.idempotency_key}",
        f"Banco Origen: {transferencia.sender_bank}",
        f"BIC Origen: {transferencia.sender_bic}",
        f"IBAN Origen: {transferencia.sender_iban}",
        f"Propietario: {transferencia.sender_name}",
        
        f"Banco Destino: {transferencia.recipient_bank}",
        f"BIC Destino: {transferencia.recipient_bic}",
        f"IBAN Destino: {transferencia.recipient_iban}",
        f"Beneficiario: {transferencia.recipient_name}",
        
        f"Monto: {transferencia.amount} {transferencia.currency}",
        f"Estado: {transferencia.status}",
        f"ID Transacción SWIFT: {transferencia.SEPA3_id}",
        f"Fecha: {transferencia.execution_date.strftime('%d/%m/%Y %H:%M:%S')}",
    ]

    y = 720
    for detalle in detalles:
        c.drawString(100, y, detalle)
        y -= 20

    c.save()
    return pdf_path



