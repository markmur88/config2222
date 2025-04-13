import logging
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from api.sct.models import SepaCreditTransferRequest
logger = logging.getLogger("bank_services")


def generate_sepa_xml(transfers: SepaCreditTransferRequest) -> str:
    """
    Genera un archivo XML SEPA Credit Transfer basado en una instancia de SepaCreditTransferRequest.
    """
    try:
        # Crear el elemento raíz del XML
        root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
        cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")

        # Grupo de encabezado
        grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
        ET.SubElement(grp_hdr, "MsgId").text = str(transfers.idempotency_key)
        ET.SubElement(grp_hdr, "CreDtTm").text = datetime.now().isoformat()
        ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
        ET.SubElement(grp_hdr, "CtrlSum").text = str(transfers.instructed_amount)
        initg_pty = ET.SubElement(grp_hdr, "InitgPty")
        ET.SubElement(initg_pty, "Nm").text = transfers.debtor_name

        # Información de pago
        pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
        ET.SubElement(pmt_inf, "PmtInfId").text = str(transfers.payment_id)
        ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
        ET.SubElement(pmt_inf, "BtchBookg").text = "false"
        ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
        ET.SubElement(pmt_inf, "CtrlSum").text = str(transfers.instructed_amount)

        # Configuración para Instant SEPA Credit Transfer
        pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
        ET.SubElement(pmt_tp_inf, "InstrPrty").text = "HIGH"
        svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
        ET.SubElement(svc_lvl, "Cd").text = "SEPA"

        # Deudor
        dbtr = ET.SubElement(pmt_inf, "Dbtr")
        ET.SubElement(dbtr, "Nm").text = transfers.debtor_name
        # Dirección del deudor
        dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
        ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transfers.debtor_adress_street_and_house_number
        ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transfers.debtor_adress_zip_code_and_city
        ET.SubElement(dbtr_pstl_adr, "Ctry").text = transfers.debtor_adress_country
        dbtr_pty = ET.SubElement(pmt_inf, "DbtrAcct")
        ET.SubElement(dbtr_pty, "Id").text = transfers.debtor_account_iban
        dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
        ET.SubElement(dbtr_agt, "FinInstnId").text = transfers.debtor_account_bic

        # Información de la transacción
        cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
        pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
        ET.SubElement(pmt_id, "EndToEndId").text = str(transfers.payment_identification_end_to_end_id)

        # Cantidad
        amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
        ET.SubElement(amt, "InstdAmt", Ccy=transfers.instructed_currency).text = str(transfers.instructed_amount)

        # Acreedor
        cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
        ET.SubElement(cdtr, "Nm").text = transfers.creditor_name
        # Dirección del acreedor
        cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
        ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transfers.creditor_adress_street_and_house_number
        ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transfers.creditor_adress_zip_code_and_city
        ET.SubElement(cdtr_pstl_adr, "Ctry").text = transfers.creditor_adress_country
        # Cuenta del acreedor
        cdtr_pty = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
        cdtr_pty_id = ET.SubElement(cdtr_pty, "Id")
        ET.SubElement(cdtr_pty_id, "IBAN").text = transfers.creditor_account_iban
        ET.SubElement(cdtr_pty, "Ccy").text = transfers.creditor_account_currency
        # Agente del acreedor
        cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
        cdtr_agt_fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
        ET.SubElement(cdtr_agt_fin_instn_id, "BIC").text = transfers.creditor_account_bic

        # Información adicional
        rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
        if transfers.remittance_information_structured:
            ET.SubElement(rmt_inf, "Strd").text = transfers.remittance_information_structured
        if transfers.remittance_information_unstructured:
            ET.SubElement(rmt_inf, "Ustrd").text = transfers.remittance_information_unstructured

        # Convertir el árbol XML a una cadena
        xml_string = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
        return xml_string

    except Exception as e:
        logger.error(f"Error al generar el archivo XML: {str(e)}", exc_info=True)
        raise
    