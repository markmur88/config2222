from rest_framework.exceptions import APIException
import logging  # Importar el módulo de logging
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from django.conf import settings
import requests
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, generics

from api.sct.process_deutsche_bank import deutsche_bank_transfer
from api.sct.models import SepaCreditTransferRequest
from api.sct.serializers import SepaCreditTransferRequestSerializer
from api.sct.generate_pdf import generar_pdf_transferencia
from api.sct.generate_xml import generate_sepa_xml

from dotenv import load_dotenv
load_dotenv()


# Configurar el logger
logger = logging.getLogger(__name__)

# Constantes
ERROR_KEY = "error"
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = 'idempotency_key'







def process_bank_transfer1(transfers, idempotency_key):
    """
    Procesa una transferencia bancaria exclusivamente para Deutsche Bank.
    """
    try:
        response = deutsche_bank_transfer(idempotency_key, transfers)
        if "error" not in response:
            return {
                "transaction_status": "PDNG",
                "payment_id":str(transfers.payment_id),
                "auth_id":str(transfers.auth_id),
                "bank_response": response,
            }
        return response
    except Exception as e:
        logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
        raise APIException("Error procesando la transferencia bancaria.")


def process_bank_transfer(idempotency_key, transfers):
    try:
        # # Ruta del archivo XML
        # xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
        # if not os.path.exists(xml_path):
        #     raise FileNotFoundError(f"El archivo XML {xml_path} no existe.")

        # Generar el archivo XML si no existe
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
        if not os.path.exists(xml_path):
            sepa_xml = generate_sepa_xml(transfers)
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

        # Leer el contenido del archivo XML
        with open(xml_path, "r") as xml_file:
            xml_content = xml_file.read()

        # Enviar el XML al banco
        response = requests.post(
            url=settings.BANK_API_URL,
            headers={"Content-Type": "application/xml"},
            data=xml_content
        )

        # Verificar la respuesta del banco
        if response.status_code != 200:
            return {"error": f"Error al enviar el XML al banco: {response.text}"}

        # Procesar la respuesta del banco (asumiendo que es XML)
        bank_response = response.text
        return {"success": True, "bank_response": bank_response}

    except Exception as e:
        logger.error(f"Error en process_bank_transfer: {str(e)}", exc_info=True)
        return {"error": str(e)}


def process_bank_transfer11(idempotency_key, transfers):
    """
    Procesa una transferencia bancaria utilizando un archivo XML generado para SEPA.
    """
    try:
        # Ruta del archivo XML
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")

        # Generar el archivo XML si no existe
        if not os.path.exists(xml_path):
            try:
                sepa_xml = generate_sepa_xml(transfers)
                with open(xml_path, "w", encoding="utf-8") as xml_file:
                    os.chmod(xml_path, 0o600)  # Permisos restrictivos
                    xml_file.write(sepa_xml)
            except Exception as e:
                logger.error(f"Error al generar o guardar el archivo XML: {str(e)}", exc_info=True)
                return {"error": "Error al generar el archivo XML"}

        # Leer el contenido del archivo XML
        try:
            with open(xml_path, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
        except Exception as e:
            logger.error(f"Error al leer el archivo XML: {str(e)}", exc_info=True)
            return {"error": "Error al leer el archivo XML"}

        # Enviar el XML al banco
        try:
            response = requests.post(
                url=settings.BANK_API_URL,
                headers={"Content-Type": "application/xml"},
                data=xml_content
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar el XML al banco: {str(e)}", exc_info=True)
            return {"error": "Error al enviar el XML al banco"}

        # Verificar la respuesta del banco
        if response.status_code != 200:
            logger.error(f"Respuesta del banco con error: {response.text}")
            return {"error": f"Error al enviar el XML al banco: {response.text}"}

        # Procesar la respuesta del banco
        try:
            bank_response = response.text  # Asumiendo que es texto o XML
            return {"success": True, "bank_response": bank_response}
        except Exception as e:
            logger.error(f"Error procesando la respuesta del banco: {str(e)}", exc_info=True)
            return {"error": "Error procesando la respuesta del banco"}

    except Exception as e:
        logger.error(f"Error inesperado en process_bank_transfer para idempotency_key {idempotency_key}: {str(e)}", exc_info=True)
        return {"error": str(e)}
      