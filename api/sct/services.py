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


def error_response(message, status_code):
    response = Response({"error": message}, status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response


def success_response(data, status_code):
    response = Response(data, status=status_code)
    response.accepted_renderer = JSONRenderer()
    response.accepted_media_type = "application/json"
    response.renderer_context = {}
    return response


def get_existing_record(model, key_value, key_field):
    filter_kwargs = {key_field: key_value}
    return model.objects.filter(**filter_kwargs).first()


def get_deutsche_bank_token():
    url = f"{settings.DEUTSCHE_BANK_API_URL}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.DEUTSCHE_BANK_CLIENT_ID,
        "client_secret": settings.DEUTSCHE_BANK_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error obteniendo token de Deutsche Bank: {e}, Response: {response.text if response else 'N/A'}")
        return {"error": "No se pudo obtener el token de acceso"}


def deutsche_bank_transfer11(idempotency_key, transfer_request):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # token_response = get_deutsche_bank_token()
        # access_token = token_response.get("access_token")
        
        access_token = os.getenv("ACCESS_TOKEN")

        
        # if not access_token:
        #     logger.error(f"Error obteniendo token de Deutsche Bank: {token_response.get('error', 'Respuesta desconocida')}")
        #     return {"error": "No se pudo obtener el token de acceso de Deutsche Bank"}

        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            # "otp": "SEPA_TRANSFER_GRANT"
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            # 'PSU-ID': 'YOUR_USER_ID',
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'            
        }

        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode":transfer_request.purpose_code,
            "requestedExecutionDate":transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.debtor_adress_zip_code_and_city,
                    "country":transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfer_request.debtor_account_iban,
                "bic":transfer_request.debtor_account_bic,
                "currency":transfer_request.debtor_account_currency
            },
            "creditor": {
                "name":transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.creditor_adress_zip_code_and_city,
                    "country":transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfer_request.creditor_account_iban,
                "bic":transfer_request.creditor_account_bic,
                "currency":transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfer_request.payment_identification_end_to_end_id),
                "instructionId":str(transfer_request.payment_identification_instruction_id)
            },
            "instructedAmount": {
                "amount":str(transfer_request.instructed_amount),
                "currency":transfer_request.instructed_currency
            },
            "remittanceInformationStructured":transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured":transfer_request.remittance_information_unstructured
        }

        SepaCreditTransferUpdateScaRequest = {
            "action": "CREATE",
            "authId":transfer_request.auth_id,
        }

        SepaCreditTransferResponse = {
            "transactionStatus":transfer_request.transaction_status,
            "paymentId":transfer_request.payment_id,
            "authId":transfer_request.auth_id
        }

        SepaCreditTransferDetailsResponse = {
            "transactionStatus":transfer_request.transaction_status,
            "paymentId":transfer_request.payment_id,
            "requestedExecutionDate":transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.debtor_adress_zip_code_and_city,
                    "country":transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfer_request.debtor_account_iban,
                "bic":transfer_request.debtor_account_bic,
                "currency":transfer_request.debtor_account_currency
            },
            "creditor": {
                "name":transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.creditor_adress_zip_code_and_city,
                    "country":transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfer_request.creditor_account_iban,
                "bic":transfer_request.creditor_account_bic,
                "currency":transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfer_request.payment_identification_end_to_end_id),
                "instructionId":str(transfer_request.payment_identification_instruction_id)
            },
            "instructedAmount": {
                "amount":str(transfer_request.instructed_amount),
                "currency":transfer_request.instructed_currency
            },
            "remittanceInformationStructured":transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured":transfer_request.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "SepaCreditTransferUpdateScaRequest": SepaCreditTransferUpdateScaRequest,
            "SepaCreditTransferResponse": SepaCreditTransferResponse,
            "SepaCreditTransferDetailsResponse": SepaCreditTransferDetailsResponse,
            "bank_response": response.json()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}

    except Exception as e:
        logger.error(f"Error inesperado en Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Error inesperado: {str(e)}"}


def deutsche_bank_transfer1(idempotency_key, transfer_request):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        access_token = os.getenv("ACCESS_TOKEN")

        
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            "otp": "SEPA_TRANSFER_GRANT"
        }

        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode":transfer_request.purpose_code,
            "requestedExecutionDate":transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name":transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.debtor_adress_zip_code_and_city,
                    "country":transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban":transfer_request.debtor_account_iban,
                "bic":transfer_request.debtor_account_bic,
                "currency":transfer_request.debtor_account_currency
            },
            "creditor": {
                "name":transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber":transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity":transfer_request.creditor_adress_zip_code_and_city,
                    "country":transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban":transfer_request.creditor_account_iban,
                "bic":transfer_request.creditor_account_bic,
                "currency":transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId":transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId":str(transfer_request.payment_identification_end_to_end_id),
                "instructionId":str(transfer_request.payment_identification_instruction_id)
            },
            "instructedAmount": {
                "amount":str(transfer_request.instructed_amount),
                "currency":transfer_request.instructed_currency
            },
            "remittanceInformationStructured":transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured":transfer_request.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "bank_response": response.json()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}

    except Exception as e:
        logger.error(f"Error inesperado en Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Error inesperado: {str(e)}"}


def deutsche_bank_transfer(idempotency_key, transfer_request):
    """
    Procesa una transferencia bancaria utilizando los datos de SepaCreditTransferRequest.
    """
    try:
        # Si transfer_request es un UUID, buscar el objeto correspondiente
        if isinstance(transfer_request, uuid.UUID):
            transfer_request = SepaCreditTransferRequest.objects.filter(id=transfer_request).first()
            if not transfer_request:
                raise ValueError("No se encontró una transferencia con el ID proporcionado.")
            
            
        access_token = os.getenv("ACCESS_TOKEN")
        
        url = f"{settings.DEUTSCHE_BANK_API_URL}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "idempotency-id": str(idempotency_key),
            'X-Request-ID': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
            'PSU-ID': '02569S',
            'PSU-IP-Address': '193.150.166.1'            
        }

        # Construir los datos de la transferencia
        SepaCreditTransferRequest = {
            "purposeCode": transfer_request.purpose_code,
            "requestedExecutionDate": transfer_request.requested_execution_date.strftime("%Y-%m-%d"),
            "debtor": {
                "name": transfer_request.debtor_name,
                "address": {
                    "streetAndHouseNumber": transfer_request.debtor_adress_street_and_house_number,
                    "zipCodeAndCity": transfer_request.debtor_adress_zip_code_and_city,
                    "country": transfer_request.debtor_adress_country
                }
            },
            "debtorAccount": {
                "iban": transfer_request.debtor_account_iban,
                "bic": transfer_request.debtor_account_bic,
                "currency": transfer_request.debtor_account_currency
            },
            "creditor": {
                "name": transfer_request.creditor_name,
                "address": {
                    "streetAndHouseNumber": transfer_request.creditor_adress_street_and_house_number,
                    "zipCodeAndCity": transfer_request.creditor_adress_zip_code_and_city,
                    "country": transfer_request.creditor_adress_country
                }
            },
            "creditorAccount": {
                "iban": transfer_request.creditor_account_iban,
                "bic": transfer_request.creditor_account_bic,
                "currency": transfer_request.creditor_account_currency
            },
            "creditorAgent": {
                "financialInstitutionId": transfer_request.creditor_agent_financial_institution_id
            },
            "paymentIdentification": {
                "endToEndId": str(transfer_request.payment_identification_end_to_end_id),
                "instructionId": str(transfer_request.payment_identification_instruction_id)
            },
            "instructedAmount": {
                "amount": str(transfer_request.instructed_amount),
                "currency": transfer_request.instructed_currency
            },
            "remittanceInformationStructured": transfer_request.remittance_information_structured,
            "remittanceInformationUnstructured": transfer_request.remittance_information_unstructured
        }

        # Enviar la solicitud al banco
        response = requests.post(url, json=SepaCreditTransferRequest, headers=headers)
        response.raise_for_status()

        # Retornar las respuestas organizadas
        return {
            "SepaCreditTransferRequest": SepaCreditTransferRequest,
            "bank_response": response.json()
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTPError en Deutsche Bank: {e}, Response: {response.text}")
        return {"error": f"HTTPError: {response.text}"}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error en conexión con Deutsche Bank: {e}")
        return {"error": f"RequestException: {str(e)}"}

    except Exception as e:
        logger.error(f"Error inesperado en Deutsche Bank: {str(e)}", exc_info=True)
        return {"error": f"Error inesperado: {str(e)}"}
    

def process_bank_transfer1(transfer_data, idempotency_key):
    """
    Procesa una transferencia bancaria exclusivamente para Deutsche Bank.
    """
    try:
        response = deutsche_bank_transfer(idempotency_key, transfer_data)
        if "error" not in response:
            return {
                "transaction_status": "ACCP",
                "payment_id":str(transfer_data.payment_id),
                "auth_id":str(transfer_data.auth_id),
                "bank_response": response,
            }
        return response
    except Exception as e:
        logger.error(f"Error procesando transferencia bancaria: {str(e)}", exc_info=True)
        raise APIException("Error procesando la transferencia bancaria.")


def process_bank_transfer(idempotency_key, transfer):
    try:
        # # Ruta del archivo XML
        # xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
        # if not os.path.exists(xml_path):
        #     raise FileNotFoundError(f"El archivo XML {xml_path} no existe.")

        # Generar el archivo XML si no existe
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
        if not os.path.exists(xml_path):
            sepa_xml = generate_sepa_xml(transfer)
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


def process_bank_transfer11(idempotency_key, transfer):
    try:
        # Ruta del archivo XML
        xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")

        # Generar el archivo XML si no existe
        if not os.path.exists(xml_path):
            try:
                sepa_xml = generate_sepa_xml(transfer)
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


class ProcessTransferView12(APIView):
    def post(self, request, idempotency_key):
        try:
            # Buscar la transferencia por idempotency_key
            transfer = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)

            # Generar el archivo XML si no existe
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfer.idempotency_key}.xml")
            if not os.path.exists(xml_path):
                sepa_xml = generate_sepa_xml(transfer)
                with open(xml_path, "w") as xml_file:
                    xml_file.write(sepa_xml)

            # Enviar el XML al banco y procesar la respuesta
            bank_response = process_bank_transfer(idempotency_key, transfer)

            # Verificar si hubo un error en la respuesta del banco
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)

            # Actualizar el estado de la transferencia
            transfer.transaction_status = "ACCP"
            transfer.save()

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response["bank_response"]
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
# sct_list0
class SCTCreateView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SepaCreditTransferRequestSerializer

    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = self.serializer_class(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # @swagger_auto_schema(operation_description="Create a transfer", request_body=SepaCreditTransferRequestSerializer)
    def post(self, request):
        # Validar datos de entrada
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        try:
            # Crear y guardar la transferencia en la base de datos
            transfer = serializer.save(transaction_status="PDNG")

            # Generar XML SEPA
            sepa_xml = generate_sepa_xml(transfer)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            xml_filename = f"sepa_{transfer.id}_{timestamp}.xml"
            xml_path = os.path.join(settings.MEDIA_ROOT, xml_filename)
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            # Generar PDF de la transferencia
            pdf_path = generar_pdf_transferencia(transfer)

            # Procesar transferencia bancaria
            bank_response = deutsche_bank_transfer(None, transfer)

            # Actualizar el estado de la transacción a "ACCP" si el banco la procesa correctamente
            transfer.transaction_status = "ACCP"
            transfer.save()

            # Obtener la lista de transferencias existentes
            transfers = SepaCreditTransferRequest.objects.all()
            transfers_serializer = self.serializer_class(transfers, many=True)
            
            # Retornar respuesta exitosa
            return success_response(
                {
                    "transfer_id": transfer.id,
                    "transaction_status": transfer.transaction_status,
                    "sepa_xml_path": xml_path,
                    "pdf_path": pdf_path,
                    "bank_response": bank_response,
                    "transfers": transfers_serializer.data,                    
                },
                status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error creando transferencia: {str(e)}", exc_info=True)
            return error_response("Error inesperado al crear la transferencia", status.HTTP_500_INTERNAL_SERVER_ERROR)


# sct_list1
class SCTList(generics.ListCreateAPIView):
    queryset = SepaCreditTransferRequest.objects.all()
    serializer_class = SepaCreditTransferRequestSerializer


# sct_list2
class SCTView(APIView):
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)
        existing_transaction = SepaCreditTransferRequest.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transaction:
            return Response({"message": "Duplicate transaction", "transaction_id": existing_transaction.id},
                            status=status.HTTP_200_OK)
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(idempotency_key=idempotency_key)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# sct_list3
class SepaCreditTransferCreateView3(APIView):
    model = SepaCreditTransferRequest
    fields = '__all__'
    
    def get(self, request):
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = SepaCreditTransferRequestSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SepaCreditTransferRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {
                "transaction_status": "PDNG",
                "payment_id": "generated-payment-id",
                "auth_id": "generated-auth-id"
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# sct_list4
class SCTLView(APIView):
    """
    View para listar, crear y manejar transferencias SEPA.
    """
    permission_classes = [AllowAny]
    serializer_class = SepaCreditTransferRequestSerializer

    def get(self, request):
        """
        Lista todas las transferencias SEPA.
        """
        transfers = SepaCreditTransferRequest.objects.all()
        serializer = self.serializer_class(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Crea una nueva transferencia SEPA.
        """
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            return Response({"error": "Idempotency-Key header is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si ya existe una transacción con la misma clave de idempotencia
        existing_transaction = SepaCreditTransferRequest.objects.filter(idempotency_key=idempotency_key).first()
        if existing_transaction:
            return Response(
                {"message": "Duplicate transaction", "transaction_id": existing_transaction.id},
                status=status.HTTP_200_OK
            )

        # Validar y guardar la nueva transferencia
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            transfer = serializer.save(idempotency_key=idempotency_key, transaction_status="ACCP")

            try:
                # Generar XML SEPA
                sepa_xml = generate_sepa_xml(transfer)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                xml_filename = f"sepa_{transfer.id}_{timestamp}.xml"
                xml_path = os.path.join(settings.MEDIA_ROOT, xml_filename)
                with open(xml_path, "w") as xml_file:
                    xml_file.write(sepa_xml)

                # Generar PDF de la transferencia
                pdf_path = generar_pdf_transferencia(transfer)

                # Procesar transferencia bancaria
                bank_response = deutsche_bank_transfer(idempotency_key, transfer)

                # Actualizar el estado de la transacción a "ACCP" si el banco la procesa correctamente
                transfer.transaction_status = "ACCP"
                transfer.save()

                # Retornar respuesta exitosa
                return Response(
                    {
                        "transfer_id": transfer.id,
                        "transaction_status": transfer.transaction_status,
                        "sepa_xml_path": xml_path,
                        "pdf_path": pdf_path,
                        "bank_response": bank_response,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
                return Response(
                    {"error": "Error inesperado al procesar la transferencia"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)