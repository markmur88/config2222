import os
import xml.etree.ElementTree as ET
from datetime import datetime
from api.sct.models import SepaCreditTransferRequest


def generate_sepa_xml(transfer_request: SepaCreditTransferRequest) -> str:
    """
    Genera un archivo XML SEPA Credit Transfer basado en una instancia de SepaCreditTransferRequest.
    """
    # Crear el elemento raíz del XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")

    # Grupo de encabezado
    grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = str(transfer_request.idempotency_key)
    ET.SubElement(grp_hdr, "CreDtTm").text = datetime.now().isoformat()
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
    ET.SubElement(grp_hdr, "CtrlSum").text = str(transfer_request.instructed_amount)
    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    ET.SubElement(initg_pty, "Nm").text = transfer_request.debtor_name

    # Información de pago
    pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = str(transfer_request.payment_id)
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, "BtchBookg").text = "false"
    ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
    ET.SubElement(pmt_inf, "CtrlSum").text = str(transfer_request.instructed_amount)

    # Configuración para Instant SEPA Credit Transfer
    pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
    ET.SubElement(pmt_tp_inf, "InstrPrty").text = "HIGH"
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    ET.SubElement(svc_lvl, "Cd").text = "SEPA"

    # Deudor
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = transfer_request.debtor_name
    # Dirección del deudor
    dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
    ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transfer_request.debtor_adress_street_and_house_number
    ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transfer_request.debtor_adress_zip_code_and_city
    ET.SubElement(dbtr_pstl_adr, "Ctry").text = transfer_request.debtor_adress_country
    dbtr_pty = ET.SubElement(pmt_inf, "DbtrAcct")
    ET.SubElement(dbtr_pty, "Id").text = transfer_request.debtor_account_iban
    dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
    ET.SubElement(dbtr_agt, "FinInstnId").text = transfer_request.debtor_account_bic
    # Información de la transacción
    cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "EndToEndId").text = str(transfer_request.payment_identification_end_to_end_id)

    # Cantidad
    amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
    ET.SubElement(amt, "InstdAmt", Ccy=transfer_request.instructed_currency).text = str(transfer_request.instructed_amount)

    # Acreedor
    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = transfer_request.creditor_name
    # Dirección del acreedor
    cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
    ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transfer_request.creditor_adress_street_and_house_number
    ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transfer_request.creditor_adress_zip_code_and_city
    ET.SubElement(cdtr_pstl_adr, "Ctry").text = transfer_request.creditor_adress_country
    # Cuenta del acreedor
    cdtr_pty = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    cdtr_pty_id = ET.SubElement(cdtr_pty, "Id")
    ET.SubElement(cdtr_pty_id, "IBAN").text = transfer_request.creditor_account_iban
    ET.SubElement(cdtr_pty, "Ccy").text = transfer_request.creditor_account_currency
    # Agente del acreedor
    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    cdtr_agt_fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    ET.SubElement(cdtr_agt_fin_instn_id, "BIC").text = transfer_request.creditor_account_bic
    ET.SubElement(cdtr_agt_fin_instn_id, "ClrSysMmbId").text = transfer_request.creditor_agent_financial_institution_id

    # Información adicional
    rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
    if transfer_request.remittance_information_structured:
        ET.SubElement(rmt_inf, "Strd").text = transfer_request.remittance_information_structured
    if transfer_request.remittance_information_unstructured:
        ET.SubElement(rmt_inf, "Ustrd").text = transfer_request.remittance_information_unstructured
    # Información adicional de la transacción
    additional_info = ET.SubElement(cdt_trf_tx_inf, "AddtlTxInf")
    ET.SubElement(additional_info, "Action").text = "CREATE"
    ET.SubElement(additional_info, "AuthId").text = transfer_request.auth_id
    ET.SubElement(additional_info, "TransactionStatus").text = transfer_request.transaction_status
    
    # Convertir el árbol XML a una cadena
    xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")

    # Guardar el archivo XML en la carpeta media
    creditor_name = transfer_request.creditor_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transfer_request.payment_id
    filename = f"{creditor_name}_{timestamp}_{payment_reference}.xml"
    media_path = os.path.join("media", filename)

    os.makedirs("media", exist_ok=True)  # Crear la carpeta media si no existe
    with open(media_path, "w", encoding="utf-8") as file:
        file.write(xml_string)

    return media_path


