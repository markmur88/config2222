from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.sct.models import (
    SepaCreditTransferRequest, SepaCreditTransferResponse, 
    SepaCreditTransferDetailsResponse, SepaCreditTransferUpdateScaRequest
)
from api.sct.process_bank import process_bank_transfer, process_bank_transfer1, process_bank_transfer11
from api.sct.serializers import (
    SepaCreditTransferRequestSerializer, SepaCreditTransferResponseSerializer, 
    SepaCreditTransferDetailsResponseSerializer, SepaCreditTransferUpdateScaRequestSerializer
)
from django.conf import settings
import os
import logging
from rest_framework.exceptions import APIException
from api.sct.services import deutsche_bank_transfer
from api.sct.generate_xml import generate_sepa_xml
from api.sct.generate_pdf import generar_pdf_transferencia
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from api.sct.forms import SepaCreditTransferRequestForm
from uuid import uuid4
from datetime import date
from django.http import FileResponse, HttpResponseNotFound

logger = logging.getLogger("bank_services")
IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_HEADER_KEY = "idempotency_key"
ERROR_KEY = "error"


class ProcessTransferView1(APIView):
    def get(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfers.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfers)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfers.transaction_status = "ACCP"
            transfers.save()
            return Response({"message": "Transferencia procesada exitosamente.", "bank_response": bank_response}, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView11(APIView):
    def get(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfers.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfers)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfers.transaction_status = "ACCP"
            transfers.save()
            # Generar el archivo XML
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            logger.error(f"Transferencia con idempotency_key {idempotency_key} no encontrada.", exc_info=True)  # Agregado
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado al procesar la transferencia: {str(e)}", exc_info=True)  # Agregado
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView2(APIView):
    def get(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(id=idempotency_key)
            idempotency_key = transfers.idempotency_key
            bank_response = process_bank_transfer(idempotency_key, transfers)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfers.transaction_status = "ACCP"
            transfers.save()
            sepa_xml = generate_sepa_xml(transfers)
            if not os.path.exists(sepa_xml):
                return Response({"error": "No se pudo generar el archivo XML."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            with open(sepa_xml, "r", encoding="utf-8") as xml_file:
                xml_content = xml_file.read()
            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_content": xml_content
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView3(APIView):
    def get(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, idempotency_key):
        idempotency_key = request.data.get("idempotency_key")
        if not idempotency_key:
            serializer = SepaCreditTransferRequestSerializer(data=request.data)
            if serializer.is_valid():
                transfers = serializer.save(transaction_status="PDNG")
                idempotency_key = transfers.idempotency_key
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            bank_response = process_bank_transfer(idempotency_key, transfers)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            transfers.transaction_status = "ACCP"
            transfers.save()
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)
            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView4(APIView):
    def get(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key=None):
        # Obtener idempotency_key desde los datos o el argumento
        if not idempotency_key:
            idempotency_key = request.data.get("idempotency_key")
        
        if not idempotency_key:
            serializer = SepaCreditTransferRequestSerializer(data=request.data)
            if serializer.is_valid():
                #transfer = serializer.save(transaction_status="PDNG")
                transfers = serializer.save(transaction_status="ACCP")
                idempotency_key = transfers.idempotency_key
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            bank_response = process_bank_transfer(transfers, idempotency_key)
            if "error" in bank_response:
                return Response({"error": bank_response["error"]}, status=status.HTTP_400_BAD_REQUEST)
            
            transfers.transaction_status = "ACCP"
            transfers.save()

            # Generar el archivo XML
            sepa_xml = generate_sepa_xml(transfers)
            xml_path = os.path.join(settings.MEDIA_ROOT, f"sepa_{transfers.idempotency_key}.xml")
            with open(xml_path, "w") as xml_file:
                xml_file.write(sepa_xml)

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response": bank_response,
                "xml_path": xml_path
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessTransferView12(APIView):
    def get(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)
            serializer = SepaCreditTransferRequestSerializer(transfers)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al obtener los detalles de la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, idempotency_key):
        try:
            transfers = SepaCreditTransferRequest.objects.get(idempotency_key=idempotency_key)

            # Procesar con process_bank_transfer
            bank_response_1 = process_bank_transfer1(idempotency_key, transfers)

            # Verificar si hubo un error en el primer procesamiento
            if "error" in bank_response_1:
                return Response({"error": bank_response_1["error"]}, status=status.HTTP_400_BAD_REQUEST)

            # Procesar con process_bank_transfer1
            bank_response_2 = process_bank_transfer11(transfers, idempotency_key)

            # Verificar si hubo un error en el segundo procesamiento
            if "error" in bank_response_2:
                return Response({"error": bank_response_2["error"]}, status=status.HTTP_400_BAD_REQUEST)

            # Actualizar el estado de la transferencia
            transfers.transaction_status = "ACCP"
            transfers.save()

            return Response({
                "message": "Transferencia procesada exitosamente.",
                "bank_response_1": bank_response_1,
                "bank_response_2": bank_response_2
            }, status=status.HTTP_200_OK)
        except SepaCreditTransferRequest.DoesNotExist:
            return Response({"error": "Transferencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error procesando transferencia: {str(e)}", exc_info=True)
            return Response({"error": "Error inesperado al procesar la transferencia."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)